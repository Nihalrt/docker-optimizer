import os
import re
import docker
from pathlib import Path
from docker.errors import APIError
from collections import defaultdict


class DockerfileAnalyzer:
    def __init__(self, dockerfile_path):
        self.dockerfile_path = dockerfile_path
        self.lines = self._read_dockerfile()
        self.stage_count = self._count_stages()

    def _read_dockerfile(self):
        """Reads Dockerfile and returns lines."""
        if not os.path.exists(self.dockerfile_path):
            raise FileNotFoundError(f"Dockerfile not found at {self.dockerfile_path}")

        with open(self.dockerfile_path, "r") as file:
            return file.readlines()

    def _count_stages(self):
        """Counts the number of build stages in the Dockerfile."""
        return sum(1 for line in self.lines if line.strip().startswith('FROM'))

    def analyze(self):
        """Analyzes Dockerfile and returns optimization suggestions."""
        issues = []
        checks = [
            (self._detect_unoptimized_base_image,
             "Consider using a lighter base image (e.g., alpine, slim versions)"),
            (self._detect_redundant_run_commands,
             "Combine multiple RUN statements to reduce image layers"),
            (self._detect_missing_dockerignore,
             "Add a .dockerignore file to exclude unnecessary files"),
            (self._detect_large_copy_files,
             "Avoid copying large unnecessary files into the image"),
            (self._detect_multi_stage_opportunity,
             "Use multi-stage builds to separate build and runtime environments"),
            (self._detect_unpinned_package_versions,
             "Pin package versions to ensure consistent builds"),
            (self._detect_improper_layer_ordering,
             "Optimize layer ordering to improve cache utilization"),
            (self._detect_add_vs_copy,
             "Prefer COPY over ADD unless URL fetching is required"),
            (self._detect_root_user,
             "Run container as non-root user for improved security"),
            (self._detect_duplicate_commands,
             "Remove duplicate commands to reduce layer count"),
            (self._detect_inefficient_dockerignore,
             "Improve .dockerignore with common exclusion patterns"),
            (self._detect_unused_args,
             "Remove unused ARG declarations to reduce complexity"),
            (self._detect_non_prod_dependencies,
             "Remove development dependencies from production image")
        ]

        for check, message in checks:
            if check():
                issues.append(message)

        return sorted(issues)

    def _detect_unoptimized_base_image(self):
        """Checks for heavyweight base images."""
        base_images = ['ubuntu', 'debian', 'node', 'python']
        return any(
            re.match(rf"^FROM .*{image}(:|$)", line, re.I)
            for image in base_images
            for line in self.lines
            if line.strip().startswith('FROM')
        )


    def _detect_redundant_run_commands(self):
        """Identifies mergeable RUN instructions."""
        run_count = sum(1 for line in self.lines if line.strip().startswith('RUN'))
        return run_count > 5  # More than 5 RUN commands considered excessive

    def _detect_missing_dockerignore(self):
        """Verifies .dockerignore presence."""
        return not (Path(self.dockerfile_path).parent / '.dockerignore').exists()

    def _detect_large_copy_files(self):
        """Flags large file copies (>50MB)."""
        return any(
            os.path.getsize(src) > 50 * 1024 * 1024
            for line in self.lines
            if line.strip().startswith('COPY')
            for src in re.split(r'\s+', line.strip().split(' ', 1)[1].split(' ', 1)[0])
            if os.path.exists(src)
        )

    def _detect_multi_stage_opportunity(self):
        """Identifies potential for multi-stage builds."""
        if self.stage_count >= 2:
            return False

        build_tools = ['gcc', 'make', 'maven', 'gradle', 'npm install', 'pip install']
        return any(
            any(tool in line.lower() for tool in build_tools)
            for line in self.lines
            if line.strip().startswith('RUN')
        )

    def _detect_unpinned_package_versions(self):
        """Checks for unpinned package versions."""
        patterns = [
            (r'(apt|apk|yum|dnf)\s+install', r'=\d+'),  # Package managers
            (r'(pip|pip3|npm|yarn|gem)\s+install', r'==|@'),  # Language packages
        ]
        return any(
            re.search(tool_pattern, line) and not re.search(version_pattern, line)
            for line in self.lines
            if line.strip().startswith('RUN')
            for tool_pattern, version_pattern in patterns
        )

    def _detect_improper_layer_ordering(self):
        """Detects cache-inefficient layer ordering."""
        copy_all_found = False
        for line in self.lines:
            line = line.strip()
            if line.startswith('COPY') and '. .' in line:
                copy_all_found = True
            elif copy_all_found and line.startswith('RUN'):
                return True
        return False

    def _detect_add_vs_copy(self):
        """Flags unnecessary ADD instructions."""
        return any(
            line.strip().startswith('ADD') and
            not re.search(r'(https?://|\.tar\.|\.zip$)', line)
            for line in self.lines
        )

    def _detect_root_user(self):
        """Checks for root user usage."""
        return not any(line.strip().startswith('USER') for line in self.lines)

    def _detect_duplicate_commands(self):
        """Identifies duplicate commands."""
        commands = defaultdict(int)
        for line in self.lines:
            cmd = line.strip().split(' ', 1)[0]
            if cmd in ['RUN', 'COPY', 'ADD']:
                commands[line.strip()] += 1
        return any(count > 1 for count in commands.values())

    def _detect_inefficient_dockerignore(self):
        """Checks .dockerignore effectiveness."""
        try:
            with open(Path(self.dockerfile_path).parent / '.dockerignore') as f:
                content = f.read().lower()
                return not all(pattern in content
                               for pattern in ['.git', 'node_modules', '.env', 'tmp'])
        except FileNotFoundError:
            return False

    def _detect_unused_args(self):
        """Identifies unused build arguments."""
        declared_args = set()
        used_args = set()

        for line in self.lines:
            if line.strip().startswith('ARG'):
                arg = line.strip().split(' ', 1)[1].split('=')[0].strip()
                declared_args.add(arg)
            else:
                used_args.update(re.findall(r'\$\{?(\w+)', line))

        return bool(declared_args - used_args)

    def _detect_non_prod_dependencies(self):
        """Flags development dependencies in final image."""
        if self.stage_count < 2:
            return any(
                any(dev_tool in line.lower() for dev_tool in
                    ['dev-dependencies', '--dev', 'debug', 'testing'])
                for line in self.lines
                if line.strip().startswith('RUN')
            )
        return False



class DockerImageInspector:
    """Analyzes built Docker images using Docker SDK"""

    def __init__(self, dockerfile_dir):
        self.client = docker.from_env()
        self.dockerfile_dir = str(dockerfile_dir)
        self.image = None
        self.layers = []
        self._log_buffer = []

    def _log_handler(self, chunk):
        """Handle build output in real-time"""
        if 'stream' in chunk:
            line = chunk['stream'].strip()
            if line:
                print(f"  [Docker Build] {line}")
        self._log_buffer.append(chunk)

    def build_image(self, tag='optimizer-temp'):
        try:
            print("Building temporary image... (this may take a few minutes)")
            self.image, build_logs = self.client.images.build(
                path=self.dockerfile_dir,
                dockerfile=str(Path(self.dockerfile_dir) / "Dockerfile"),
                tag=tag,
                rm=True,
                forcerm=True,
                timeout=600  # 10 minute timeout
            )
            print("Build completed successfully!")
            self._analyze_layers()
        except APIError as e:
            print("\nBuild failed with error:")
            for chunk in self._log_buffer:
                if 'error' in chunk:
                    print(chunk['error'].strip())
            raise RuntimeError(f"Docker build error: {e}")

    def _analyze_layers(self):
        """Analyzes image layer metadata"""
        if self.image:
            self.layers = self.image.history()

    def get_size_analysis(self):
        """Returns detailed size information"""
        return {
            'total_size': sum(layer['Size'] for layer in self.layers if 'Size' in layer),
            'layers': [
                {
                    'command': layer['CreatedBy'],
                    'size': layer['Size'],
                    'human_size': f"{layer['Size'] / (1024 * 1024):.1f}MB"
                }
                for layer in self.layers if 'Size' in layer
            ]
        }


if __name__ == "__main__":
    dockerfile_path = "./Dockerfile"
    analyzer = DockerfileAnalyzer(dockerfile_path)
    suggestions = analyzer.analyze()

    print("\n=== Dockerfile Optimization Suggestions ===")
    if suggestions:
        for idx, suggestion in enumerate(suggestions, 1):
            print(f"{idx}. {suggestion}")
    else:
        print("No significant optimization opportunities found!")

    try:
        print("\n=== Image Size Analysis ===")
        inspector = DockerImageInspector(str(Path(dockerfile_path).parent))

        # First: Validate Dockerfile
        print("Validating Dockerfile...")
        with open(dockerfile_path, 'r') as f:
            print("\n".join([f"  | {line.strip()}" for line in f.readlines()]))

        # Then: Build with progress
        inspector.build_image()

    except Exception as e:
        print(f"\nImage analysis unavailable: {str(e)}")