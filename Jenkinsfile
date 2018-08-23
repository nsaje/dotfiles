#!groovy
node('master') {
    stage('Setup') {
        sh 'export' // for debug purposes
        env.CACHE_DIR = "${JENKINS_HOME}/workspace/_CACHE/${JOB_NAME}"
        sh 'mkdir -p ${CACHE_DIR}'
        env.PATH = "${JENKINS_HOME}/bin/:${env.PATH}"
        env.AWS_DEFAULT_REGION="us-east-1"        
    }

    stage('Code checkout') {
        checkout scm
        // make sure we don't have leftovers from previous builds
        sh 'sudo git clean --force -d -x'

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
                        junit 'server/.junit_acceptance.xml'
                    }
                },
                'Server test': {
                    try {
                        sh 'make test_server | stdbuf -i0 -o0 -e0 tee /dev/stderr | tail -n 10 | grep "PASSED"'
                    } finally {
                        junit 'server/.junit_xml/*.xml'
                    }
                },
                'Client test': {
                    try {
                        sh 'make test_client'                     
                    } finally {
                        junit 'client/test-results.xml'
                    }
                },
                'Client build': {
                    // Client artifacts
                    sh 'make build_client'
                    // webpack sometimes build empty z1 client
                    sh """[ "\$(wc -c <client/dist/one/zemanta-one.js)" -ge 800000 ]"""
                },
                failFast: true  // if one of the parallel branches fails, fail the build right away
            )
        }
    }

    stage('Collect artifacts') {        
        sh 'make collect_server_static'
        sh './scripts/push_static_to_s3.sh'
        // restapi docs
        sh './server/restapi/docs/build-docker.sh "build-${BRANCH_NAME}.${BUILD_NUMBER}.html" && ./scripts/push_docs_to_s3.sh ./server/restapi/docs/build-${BRANCH_NAME}.${BUILD_NUMBER}.html'
        // files needed for deploy
        sh './scripts/push_artifact_to_s3.sh "docker-compose.prod.yml"'
        sh './scripts/push_artifact_to_s3.sh "docker-compose.demo.yml"'
        sh './scripts/push_artifact_to_s3.sh "docker/docker-manage-py.sh"'
        // Server
        sh 'make push'
    }   

    stage('Cleanup workspace') {
        sh 'docker-compose kill; docker-compose rm -v -f'
    }
}
