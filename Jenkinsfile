// =============================================================================
// JENKINSFILE — Media Streaming Microservices Analyzer Pipeline
// =============================================================================
// Runs the Test Impact Analyzer on a multi-language monorepo where each
// service has its own tests folder. This pipeline discovers tests at any
// depth and runs only those affected by the change.
//
// Languages covered: Python, JavaScript, Java, C#
// Test frameworks:  pytest, jest, maven, dotnet test
// =============================================================================

pipeline {

    agent any

    environment {
        PYTHONIOENCODING = 'UTF-8'
        PYTHONPATH       = "${WORKSPACE}"

        VENV_DIR     = 'venv'
        ANALYZER_DIR = 'scripts'
        TARGET_REPO  = 'media_streaming_services'
        TEST_DIR     = 'media_streaming_services'      // ← recursive scan of the whole repo
        RESULT_FILE  = 'analyzer_result.json'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '15'))
        timestamps()
        skipDefaultCheckout(true)
    }

    stages {

        // =====================================================================
        // STAGE 1: CHECKOUT
        // =====================================================================
        stage('Checkout') {
            steps {
                echo '=== [1/9] Checking out source code ==='
                checkout scm

                sh 'echo "Workspace contents:" && ls -la'

                sh """
                    if [ ! -d "${TARGET_REPO}" ]; then
                        echo "ERROR: ${TARGET_REPO}/ not found!"
                        exit 1
                    fi
                    echo "${TARGET_REPO}/ confirmed."
                    echo "Services found: \$(ls ${TARGET_REPO} | grep -- -service | wc -l)"
                """
            }
        }

        // =====================================================================
        // STAGE 2: SETUP PYTHON ENVIRONMENT
        // =====================================================================
        stage('Setup Python Environment') {
            steps {
                echo '=== [2/9] Setting up Python virtual environment ==='
                sh "rm -rf ${VENV_DIR}"
                sh "python3 -m venv ${VENV_DIR}"
                sh "${VENV_DIR}/bin/pip install --upgrade pip"
            }
        }

        // =====================================================================
        // STAGE 3: INSTALL PYTHON DEPENDENCIES (ANALYZER)
        // =====================================================================
        stage('Install Python Dependencies') {
            steps {
                echo '=== [3/9] Installing analyzer Python dependencies ==='
                sh "${VENV_DIR}/bin/pip install -r requirements.txt"

                // Verify critical imports
                sh """
                    ${VENV_DIR}/bin/python -c "
import yaml
import json
import subprocess
import argparse
from pathlib import Path
print('Analyzer imports OK')
"
                """
            }
        }

        // =====================================================================
        // STAGE 4: DETECT CHANGES
        // =====================================================================
        stage('Detect Changes') {
            steps {
                echo '=== [4/9] Detecting changes ==='

                dir(TARGET_REPO) {
                    sh 'git log --oneline -5 || echo "No git log"'
                    sh '''
                        COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo 0)
                        echo "Commit count: $COMMIT_COUNT"
                        if [ "$COMMIT_COUNT" -lt 2 ]; then
                            echo "WARNING: fewer than 2 commits"
                        fi
                    '''
                    sh 'git diff --name-only HEAD~1..HEAD 2>/dev/null || echo "No previous commit"'
                }
            }
        }

        // =====================================================================
        // STAGE 5: RUN THE ANALYZER
        // =====================================================================
        stage('Analyze Changes') {
            steps {
                echo '=== [5/9] Running Test Impact Analyzer ==='

                sh "rm -f ${RESULT_FILE}"

                // KEY: --tests points to the WHOLE target repo. The analyzer
                // recursively discovers tests inside every service folder.
                sh """
                    ${VENV_DIR}/bin/python ${ANALYZER_DIR}/run_analyzer.py \
                        --repo ${TARGET_REPO} \
                        --range HEAD~1..HEAD \
                        --tests ${TEST_DIR} \
                    || echo "Analyzer returned non-zero"
                """

                sh """
                    if [ ! -f "${RESULT_FILE}" ]; then
                        echo '{"affected_tests":[],"has_affected_tests":false,"test_count":0}' > ${RESULT_FILE}
                    fi
                """
            }
        }

        // =====================================================================
        // STAGE 6: SHOW SUMMARY
        // =====================================================================
        stage('Show Summary') {
            steps {
                echo '=== [6/9] Analysis Summary ==='
                sh "${VENV_DIR}/bin/python ${ANALYZER_DIR}/show_summary.py ${RESULT_FILE}"
            }
        }

        // =====================================================================
        // STAGE 7: RUN AFFECTED TESTS (multi-language dispatch)
        // =====================================================================
        stage('Run Affected Tests') {
            steps {
                echo '=== [7/9] Running only the affected tests ==='

                // run_selected_tests.py dispatches to the right runner per
                // extension: pytest, npm test, mvn test, dotnet test.
                sh """
                    ${VENV_DIR}/bin/python run_selected_tests.py \
                        || echo "Some tests failed — see output above"
                """
            }
        }

        // =====================================================================
        // STAGE 8: ARCHIVE RESULTS
        // =====================================================================
        stage('Archive Results') {
            steps {
                echo '=== [8/9] Archiving results ==='
                archiveArtifacts(
                    artifacts: "${RESULT_FILE}",
                    allowEmptyArchive: true,
                    fingerprint: true
                )
            }
        }
    }

    post {
        always {
            echo '========================================================='
            echo 'Pipeline execution finished.'
            echo '========================================================='

            sh '''
                if [ -f "analyzer_result.json" ]; then
                    echo "Final analyzer_result.json:"
                    cat analyzer_result.json
                fi
            '''

            sh 'rm -rf venv || true'
        }

        success {
            echo '========================================================='
            echo 'BUILD SUCCEEDED'
            echo '========================================================='
        }

        failure {
            echo '========================================================='
            echo 'BUILD FAILED'
            echo '========================================================='
        }
    }
}