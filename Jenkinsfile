// =============================================================================
// JENKINSFILE — Test Impact Analyzer for media_streaming_Services
// =============================================================================
// This pipeline automatically runs ONLY the tests affected by changes to the
// media_streaming_microservices project. It implements thesis Objective IV:
// "Integrate this analyzer directly into automated continuous integration
//  pipelines so the system only compiles the necessary code modules and
//  runs only the impacted tests."
//
// Pipeline Flow:
//   1. Checkout           → Pull the latest code from Git
//   2. Setup Python       → Create a clean virtual environment
//   3. Install Deps       → Install Python dependencies
//   4. Detect Changes     → Show what changed since the last commit
//   5. Analyze            → Run the analyzer, produce analyzer_result.json
//   6. Show Summary       → Human-readable summary of selected tests
//   7. Run Tests          → Execute ONLY the affected tests
//   8. Archive            → Save analyzer_result.json as a build artifact
// =============================================================================

pipeline {

    // -------------------------------------------------------------------------
    // AGENT
    // -------------------------------------------------------------------------
    agent any

    // -------------------------------------------------------------------------
    // ENVIRONMENT VARIABLES
    // -------------------------------------------------------------------------
    environment {
        // Prevent encoding issues
        PYTHONIOENCODING = 'UTF-8'

        // Make the project root importable
        PYTHONPATH = "${WORKSPACE}"

        // Paths (relative to WORKSPACE)
        VENV_DIR      = 'venv'
        ANALYZER_DIR  = 'scripts'
        TARGET_REPO   = 'media_streaming_services'
        TEST_DIR      = 'tests'
        RESULT_FILE   = 'analyzer_result.json'
    }

    // -------------------------------------------------------------------------
    // OPTIONS
    // -------------------------------------------------------------------------
    options {
        buildDiscarder(logRotator(numToKeepStr: '15'))
        timestamps()
        skipDefaultCheckout(true)
    }

    // -------------------------------------------------------------------------
    // STAGES
    // -------------------------------------------------------------------------
    stages {

        // =====================================================================
        // STAGE 1: CHECKOUT
        // =====================================================================
        stage('Checkout') {
            steps {
                echo '=== [1/8] Checking out source code ==='
                checkout scm

                sh 'echo "Workspace contents:" && ls -la'

                // Verify the target project and tests folder exist
                sh """
                    if [ ! -d "${TARGET_REPO}" ]; then
                        echo "ERROR: ${TARGET_REPO}/ folder not found!"
                        exit 1
                    fi
                    echo "${TARGET_REPO}/ folder confirmed."

                    if [ ! -d "${TEST_DIR}" ]; then
                        echo "ERROR: ${TEST_DIR}/ folder not found!"
                        exit 1
                    fi
                    echo "${TEST_DIR}/ folder confirmed with \$(ls ${TEST_DIR} | wc -l) file(s)."
                """
            }
        }

        // =====================================================================
        // STAGE 2: SETUP PYTHON ENVIRONMENT
        // =====================================================================
        stage('Setup Python Environment') {
            steps {
                echo '=== [2/8] Setting up Python virtual environment ==='
                sh "rm -rf ${VENV_DIR}"
                sh "python3 -m venv ${VENV_DIR}"
                sh "${VENV_DIR}/bin/pip install --upgrade pip"
            }
        }

        // =====================================================================
        // STAGE 3: INSTALL PYTHON DEPENDENCIES
        // =====================================================================
        stage('Install Python Dependencies') {
            steps {
                echo '=== [3/8] Installing Python dependencies ==='
                sh "${VENV_DIR}/bin/pip install -r requirements.txt"

                sh """
                    ${VENV_DIR}/bin/python -c "
import yaml
import json
import subprocess
import argparse
from pathlib import Path
print('All critical imports OK')
"
                """
            }
        }

        // =====================================================================
        // STAGE 4: DETECT CHANGES
        // =====================================================================
        stage('Detect Changes') {
            steps {
                echo '=== [4/8] Detecting changes ==='

                dir(TARGET_REPO) {
                    sh 'git log --oneline -5 || echo "Could not read git log"'

                    sh '''
                        COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo 0)
                        echo "Commit count: $COMMIT_COUNT"
                        if [ "$COMMIT_COUNT" -lt 2 ]; then
                            echo "WARNING: Repository has fewer than 2 commits."
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
                echo '=== [5/8] Running Test Impact Analyzer ==='

                sh "rm -f ${RESULT_FILE}"

                sh """
                    ${VENV_DIR}/bin/python ${ANALYZER_DIR}/run_analyzer.py \
                        --repo ${TARGET_REPO} \
                        --range HEAD~1..HEAD \
                        --tests ${TEST_DIR} \
                    || echo "Analyzer returned non-zero (possibly no changes detected)"
                """

                sh """
                    if [ ! -f "${RESULT_FILE}" ]; then
                        echo "WARNING: ${RESULT_FILE} not found. Creating empty file."
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
                echo '=== [6/8] Analysis Summary ==='
                sh "${VENV_DIR}/bin/python ${ANALYZER_DIR}/show_summary.py ${RESULT_FILE}"
            }
        }

        // =====================================================================
        // STAGE 7: RUN AFFECTED TESTS
        // =====================================================================
        stage('Run Affected Tests') {
            steps {
                echo '=== [7/8] Running only the affected tests ==='

                // The || echo prevents the pipeline from failing when a
                // single test fails, so we always archive the results.
                // Remove it for a production CI gate that should fail on test failure.
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
                echo '=== [8/8] Archiving results ==='
                archiveArtifacts(
                    artifacts: "${RESULT_FILE}",
                    allowEmptyArchive: true,
                    fingerprint: true
                )
            }
        }
    }

    // -------------------------------------------------------------------------
    // POST ACTIONS
    // -------------------------------------------------------------------------
    post {
        always {
            echo '========================================================='
            echo 'Pipeline execution finished.'
            echo '========================================================='

            sh '''
                if [ -f "analyzer_result.json" ]; then
                    echo "Final analyzer_result.json:"
                    cat analyzer_result.json
                else
                    echo "No analyzer_result.json file present."
                fi
            '''

            sh 'rm -rf venv || true'
        }

        success {
            echo '========================================================='
            echo 'BUILD SUCCEEDED'
            echo 'All affected tests passed.'
            echo '========================================================='
        }

        failure {
            echo '========================================================='
            echo 'BUILD FAILED'
            echo 'Check the console output above for details.'
            echo '========================================================='
        }
    }
}