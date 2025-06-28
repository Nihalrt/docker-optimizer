from flask import Flask, request, jsonify
import sys
import os

from services import DockerfileAnalyzer

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])

def analyze_dockerfile():
    
    """
    API to analyze a dockerfile
    Expects a POST request with a docker file content in the body

    """

    dockerfile_content = request.data.decode("utf-8")

    with open("temp_dockerfile", "w") as f:
        f.write(dockerfile_content)

    analyzer = DockerfileAnalyzer("temp_dockerfile")

    suggestions = analyzer.analyze()

    os.remove("temp_dockerfile")

    return jsonify({"suggestions" : suggestions })


if __name__ == '__main__':
    app.run(debug=True)



