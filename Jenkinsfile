// def changeLogSets = currentBuild.changeSets
// for (int i = 0; i < changeLogSets.size(); i++) {
//   def entries = changeLogSets[i].items
//   for (int j = 0; j < entries.length; j++) {
//     def entry = entries[j]
//     def files = new ArrayList(entry.affectedFiles)
//     for (int k = 0; k < files.size(); k++) {
//       def file = files[k]
//       println file.path
//       println "file.path"
//     }
//   }
// }




@NonCPS
def showChangeLogs() {
  def changeLogSets = currentBuild.rawBuild.changeSets
  for (int i = 0; i < changeLogSets.size(); i++) {
     def entries = changeLogSets[i].items
     for (int j = 0; j < entries.length; j++) {
          def entry = entries[j]
          echo "${entry.commitId} by ${entry.author} on ${new Date(entry.timestamp)}: ${entry.msg}"
          def files = new ArrayList(entry.affectedFiles)
          for (int k = 0; k < files.size(); k++) {
              def file = files[k]
              echo "  ${file.editType.name} ${file.path}"
          }
      }
  }
}

showChangeLogs()

// @NonCPS
// def branchForBuild( build ) {
//   def scmAction = build?.actions.find { action -> action instanceof jenkins.scm.api.SCMRevisionAction }
//   println scmAction?.revision?.head?.getName()
//   return scmAction?.revision?.head?.getName()
// }

// lastChanges() //will use defaults
// https://plugins.jenkins.io/last-changes

def masterIP = InetAddress.localHost.hostAddress
println "Master located at ${masterIP}"

// echo vm.max_map_count=262144 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p    # for Elastic Compute
// echo fs.inotify.max_user_watches=582222 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p    # for NodeJS to watch more files

// sudo apt-get install jq

// curl -sL https://deb.nodesource.com/setup_11.x | sudo -E bash -
// sudo apt-get install -y nodejs

// curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
// echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
// sudo apt-get update && sudo apt-get install yarn

// sudo apt install tmuxinator tmux

pipeline {
  agent {
    label "development"
  }
  parameters {
    string(name: 'Greeting', defaultValue: InetAddress.localHost.hostAddress, description: 'How should I greet the world?')
  }
  environment {
    CI = 'true'
    MASTER_IP = "${InetAddress.localHost.hostAddress}"
    HOST_IP = "localhost"
    WORKSPACE = pwd()
    // BRANCH_NAME2 = "${env.BRANCH_NAME == 'trunk' ? '': env.BRANCH_NAME}"
  }
  stages {
    stage('Start') {
      steps {
        echo "${params.Greeting} World! ${env.HOST_IP}"
      }
    }
    stage('Install Docker') {
      steps {
        sh "sudo jenkins/install_docker.sh"
      }
    }
    stage('Install ElasticSearch') {
      when {
        expression { // Skip if elasticsearch container already exists
          sh (
            script: "sudo docker ps | grep elasticsearch",
            returnStatus: true
          ) != 0
        }
      }
      steps {
        dir('image-archive/elastic-search/') {
          sh 'sudo docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -v `pwd`/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml docker.elastic.co/elasticsearch/elasticsearch:6.6.0'
          sh """bash -c 'while [[ "`curl -v -s -o /dev/null -w ''%{http_code}'' localhost:9200`" != "200" ]]; do echo "trying again"; sleep 5; done; curl localhost:9200; echo "ELASTIC UP"'"""
          sh 'sudo docker logs elasticsearch'
          sh './init_elastic.sh'
          // sh 'sudo docker run -p 1358:1358 -d appbaseio/dejavu'
        }
      }
      // post {
      //   failure {
      //       sh 'sudo docker rm -f elasticsearch'
      //   }
      // }
    }
    stage('Install DWV') {
      steps {
        dir('image-archive/dwv/') {
          sh 'yarn install'
          sh 'yarn run start &'
          sh """bash -c 'while [[ "`curl -v -s -o /dev/null -w ''%{http_code}'' localhost:8080`" != "200" ]]; do echo "trying again"; sleep 5; done; curl localhost:8080; echo "DWV UP"'"""
        }
      }
    }
    stage('Install ReactiveSearch') {
      steps {
        dir('image-archive/reactive-search/') {
          sh 'npm install'
          sh 'npm run dev &'
          sh """bash -c 'while [[ "`curl -v -s -o /dev/null -w ''%{http_code}'' localhost:3000`" != "200" ]]; do echo "trying again"; sleep 5; done; curl localhost:3000; echo "ReactiveSearch UP"'"""
        }
      }
    }
    stage('Load Sample Images') {
      steps {
        dir('image-archive/de-id/') {
          sh 'npm install'
        }
      }
    }
    stage('Start Tmux') {
      steps {
        dir('image-archive/') {
          sh "tmuxinator"
        }
      }
    }
  }

  // post {
    // Always runs. And it runs before any of the other post conditions.
    // always {
      // Let's wipe out the workspace before we finish!
      // deleteDir()
    // }
    
    // Mail disabled because of error:
    // javax.mail.MessagingException: Could not connect to SMTP host: localhost, port: 25;
    // success {
    //   mail(from: "danielsnider12@gmail.com", 
    //        to: "danielsnider12@gmail.com", 
    //        subject: "That build passed.",
    //        body: "Nothing to see here")
    // }

    // failure {
    //   mail(from: "danielsnider12@gmail.com", 
    //        to: "danielsnider12@gmail.com", 
    //        subject: "That build failed!", 
    //        body: "Nothing to see here")
    // }
  // }

  // The options directive is for configuration that applies to the whole job.
  options {
    // For example, we'd like to make sure we only keep 10 builds at a time, so
    // we don't fill up our storage!
    buildDiscarder(logRotator(numToKeepStr:'10'))
    
    // And we'd really like to be sure that this build doesn't hang forever, so
    // let's time it out after an hour.
    timeout(time: 60, unit: 'MINUTES')
  }
}

