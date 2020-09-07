#!groovy
import hudson.model.Run
import org.jenkinsci.plugins.workflow.steps.FlowInterruptedException

def getPreviousBuildResult() {
    Run previousBuild = currentBuild.rawBuild.getPreviousBuild()
    while (previousBuild != null) {
        String result = previousBuild.result.toString()
        if (result == 'SUCCESS' || result == 'FAILURE') {
            return result
        }
        previousBuild = previousBuild.getPreviousBuild()
    }
    return ""
}

node {
    try {
        stage('Kill previous builds') {
            if (env.BRANCH_NAME != 'master') {
                Run previousBuild = currentBuild.rawBuild.getPreviousBuildInProgress()

                while (previousBuild != null) {
                    if (previousBuild.isInProgress()) {
                        echo ">> Aborting older build #${previousBuild.number}"
                        previousBuild.doTerm()
                    }

                    previousBuild = previousBuild.getPreviousBuildInProgress()
                }
            }
        }

        stage('Setup') {
            sh 'export' // for debug purposes
            env.CACHE_DIR = "${WORKSPACE}/../_CACHE/${JOB_NAME}"
            sh 'mkdir -p ${CACHE_DIR}'
            env.PATH = "${JENKINS_HOME}/bin/:${env.PATH}"
            env.AWS_DEFAULT_REGION = "us-east-1"
        }

        stage('Code checkout') {
            checkout scm
            // make sure we don't have leftovers from previous builds
            sh 'sudo git clean --force -d -x'
            env.GIT_AUTHOR = sh(script: 'git show -s --pretty=%an | head -1', returnStdout: true).trim()
            env.GIT_COMMIT_MESSAGE = sh(script: 'git show -s --pretty=%B | head -1', returnStdout: true).trim()

            // Remove old lingering containsers and volumes
            sh 'docker-compose kill; docker-compose rm -v -f'
        }

        stage('Prepare containers') {
            sh 'make rebuild_if_differ'
            sh 'make build_utils'
            sh 'make build'
        }

        withCredentials([string(credentialsId: 'z1_sentry_token', variable: 'Z1_SENTRY_TOKEN')]) {
            stage('Parallel tasks') {
                // login to ECR
                sh 'make login'

                parallel(
                        'Server lint': {
                            sh 'make lint_server'
                        },
                        'Client lint': {
                            sh 'make lint_client'
                        },
                        'Acceptance': {
                            try {
                                sh 'make test_acceptance'
                            } finally {
                                junit testResults: 'server/.junit_acceptance.xml', allowEmptyResults: true
                            }
                        },
                        'Server test': {
                            try {
                                sh 'make test_server | stdbuf -i0 -o0 -e0 tee /dev/stderr | tail -n 10 | grep "PASSED"'
                            } finally {
                                junit testResults: 'server/.junit_xml/*.xml', allowEmptyResults: true
                            }
                        },
                        'Client test': {
                            try {
                                sh 'make test_client'
                            } finally {
                                junit testResults: 'client/test-results.xml', allowEmptyResults: true
                            }
                        },
                        'Client build': {
                            // Client artifacts
                            sh 'make build_client'
                            // webpack sometimes build empty z1 client
                            sh """[ "\$(wc -c <client/dist/one/zemanta-one.js)" -ge 800000 ]"""
                        },
                        'Client styles build': {
                            // Client styles artifacts
                            sh 'make build_client_styles'
                        },
                        failFast: true  // if one of the parallel branches fails, fail the build right away
                )
            }
        }

        stage('Collect artifacts') {
            parallel(
                    'Collect static': {
                        sh 'make collect_server_static'
                        sh './scripts/push_static_to_s3.sh'
                    },
                    'Restapi docs': {
                        sh './server/restapi/docs/build-docker.sh "build-${BRANCH_NAME}.${BUILD_NUMBER}.html" && ./scripts/push_docs_to_s3.sh ./server/restapi/docs/build-${BRANCH_NAME}.${BUILD_NUMBER}.html'
                    },
                    'Artifacts': {
                        sh './scripts/push_artifact_to_s3.sh "docker-compose.prod.yml"'
                        sh './scripts/push_artifact_to_s3.sh "docker-compose.demo.yml"'
                        sh './scripts/push_artifact_to_s3.sh "docker/docker-manage-py.sh"'
                        // Server
                        sh 'make push'
                    }
            )
        }

        stage('Notify success') {
            prevResult = getPreviousBuildResult()
            if (prevResult == 'FAILURE' && env.BRANCH_NAME == 'master') {
                slackSend channel: "#rnd-z1", color: "#8CC04F", failOnError: true, message: "Build Fixed - ${env.GIT_AUTHOR}: ${env.GIT_COMMIT_MESSAGE} on ${env.JOB_BASE_NAME}/${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open Classic> | <${env.BUILD_URL}display/redirect|Open Blue Ocean>)"
            }
        }

        stage('Trigger e2e') {
            if (env.BRANCH_NAME == 'master') {
                build job: 'z1-e2e', wait: false
            }
        }
    } catch (e) {
        prevResult = getPreviousBuildResult()
        if (!(e instanceof FlowInterruptedException) && prevResult == 'SUCCESS' && env.BRANCH_NAME == 'master') {
            slackSend channel: "#rnd-z1", color: "#D54C53", failOnError: true, message: "Build Failed - ${env.GIT_AUTHOR}: ${env.GIT_COMMIT_MESSAGE} on ${env.JOB_BASE_NAME}/${env.BUILD_NUMBER} (<${env.BUILD_URL}|Open Classic> | <${env.BUILD_URL}display/redirect|Open Blue Ocean>)"
        }
        throw e
    } finally {
        stage('Cleanup workspace') {
            sh 'docker-compose kill; docker-compose rm -v -f'
        }
    }
}
