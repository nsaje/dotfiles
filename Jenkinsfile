#!groovy
node('master') {
    stage ('Setup') {
        sh 'export' // for debug puropses
        env.CACHE_DIR = "${JENKINS_HOME}/workspace/_CACHE/${JOB_NAME}"
        sh 'mkdir -p ${CACHE_DIR}'
        env.PATH = "${JENKINS_HOME}/bin/:${env.PATH}"
        env.AWS_DEFAULT_REGION="us-east-1"
    }

    stage('Code checkout') {
        checkout scm
        // make sure we don't have leftovers from previous builds
        sh 'sudo git clean --force -d -x'

        // linter
        sh 'docker build -t py-tools -f docker/Dockerfile.py-tools  docker/'
    }

    stage ('Install dependencies') {
/*
        sh 'mkdir -p ${JENKINS_HOME}/bin/'
        sh 'test ! -x ${JENKINS_HOME}/bin/docker-compose && curl -L https://github.com/docker/compose/releases/download/1.8.0/docker-compose-`uname -s`-`uname -m` > ${JENKINS_HOME}/bin/docker-compose || true'
        sh 'chmod +x ${JENKINS_HOME}/bin/docker-compose'
*/
        // for building client
        sh 'docker build -t zemanta/z1-static -f docker/Dockerfile.z1-static  docker/'

        // for building rest docs
        sh 'docker build -t zemanta/z1-aglio -f docker/Dockerfile.z1-aglio docker/'

    }

    stage ('Restore cache') {
        sh "tar -xf ${CACHE_DIR}/node_modules.tar || tar -xf ${CACHE_DIR}/../master/node_modules.tar || (echo 'No cache'; true)"
    }

    stage ('Prepare containers') {
        sh 'make rebuild_if_differ'
        sh 'make build'
    }

    stage('Run tests') {
        // login to ECR
        sh 'make login'

        // Cleanup old lingering containsers
        sh 'docker-compose kill; docker-compose rm -v -f'

        parallel(
            server: {
                try {
                    sh 'make jenkins_test | stdbuf -i0 -o0 -e0 tee /dev/stderr | tail -n 10 | grep "PASSED"'
                } finally {
                    junit 'server/.junit_xml/*.xml'
                }
            },
            client: {
                try {
                    sh """docker run \
                        --rm \
                        -u 1000 \
                        -e DISPLAY=:99 \
                        -v ${WORKSPACE}/client:/data \
                        -e CHROME_BIN=/run-chrome.sh \
                        zemanta/z1-static \
                        bash -c "Xvfb :99 -screen 0 1280x1024x24 & npm prune && npm install && bower install && grunt prod --build-number ${BUILD_NUMBER}"
                        """
                } finally {
                    junit 'client/test-results.xml'
                }
            },
            acceptance: {
                try {
                    sh 'make test_acceptance'
                } finally {
                    junit 'server/.junit_acceptance.xml'
                }
            },
            linter: {
                sh 'bash ./scripts/jenkins_lint_check.sh'
            },
            failFast: true  // if one of the parallel branches fails, fail the build right away
        )
    }

    stage('Collect artifacts') {
        // Client artifacts
        sh 'rm -rf server/static && mkdir server/static && chmod 777 server/static'
        sh '''docker-compose \
                -f docker-compose.yml \
                -f docker-compose.jenkins.yml \
                run \
                --rm \
                --entrypoint=/entrypoint_dev.sh \
                eins python manage.py collectstatic --noinput'''
//        sh 'cd client/ && git rev-parse HEAD > dist/git_commit_hash.txt && tar -pc dist/ ../server/static -zf /tmp/${BUILD_NUMBER}-client.tar.gz'
        sh '/usr/bin/test "${BRANCH_NAME}" == "master" && ./scripts/push_static_to_s3.sh || true'
        // restapi docs
        sh './server/restapi/docs/build-docker.sh "build-${BRANCH_NAME}.${BUILD_NUMBER}.html" && ./scripts/push_docs_to_s3.sh ./server/restapi/docs/build-${BRANCH_NAME}.${BUILD_NUMBER}.html'
        // files needed for deploy
        sh './scripts/push_jenkins_artifact_to_s3.sh "docker-compose.prod.yml"'
        sh './scripts/push_jenkins_artifact_to_s3.sh "docker-compose.demo.yml"'
        sh './scripts/push_jenkins_artifact_to_s3.sh "docker/docker-manage-py.sh"'
        // Server
        sh 'make push'
//        step([$class: 'S3CopyArtifact', buildSelector: [$class: 'StatusBuildSelector', stable: false], excludeFilter: '', filter: 'client/dist/', flatten: false, optional: false, projectName: '', target: 'test-test/z1/'])

    }

    stage ('Save cache') {
        sh 'tar -c client/node_modules/ -f ${CACHE_DIR}/node_modules.tar'
    }

    stage ('Cleanup workspace') {
        sh 'docker-compose kill; docker-compose rm -v -f'
//        step([$class: 'WsCleanup'])
    }
}
