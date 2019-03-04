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


pipeline {
  agent {
    label "development"
  }
  parameters {
    string(name: 'Greeting', defaultValue: InetAddress.localHost.hostAddress, description: 'How should I greet the world?')
  }
  environment {
    CI = 'true'
    HOST_IP = "${InetAddress.localHost.hostAddress}"
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
        sh "jenkins/install_docker.sh"
      }
    }
    stage('Setup ElasticSearch') {
      steps {
        dir('image-archive/elastic-search/') {
          sh 'sudo docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -v `pwd`/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml docker.elastic.co/elasticsearch/elasticsearch:6.6.0'
          sh """bash -c 'while [[ "`curl -v -s -o /dev/null -w ''%{http_code}'' localhost:9200`" != "200" ]]; do echo "trying again"; sleep 5; done; curl localhost:9200; echo "ELASTIC UP"'"""
          sh 'sudo docker logs elasticsearch'
          sh 'init_elastic.sh'
          // sh 'sudo docker run -p 1358:1358 -d appbaseio/dejavu'
        }
      }
      post {
        failure {
            sh 'sudo docker rm -f elasticsearch'
        }
      }
    }
    stage('DWV') {
      steps {
        dir('image-archive/dwv/') {
          sh 'yarn install'
          sh 'yarn run start &'
          sh """bash -c 'while [[ "`curl -v -s -o /dev/null -w ''%{http_code}'' localhost:8080`" != "200" ]]; do echo "trying again"; sleep 5; done; curl localhost:8080; echo "DWV UP"'"""
        }
      }
    }
    // stage('ReactiveSearch') {
  //     steps {
      //   dir('image-archive/reactive-search/') {
    //       sh 'npm install'
    //       sh 'npm run dev &'

    //     }
    //   }
    // }
  }

  post {
    // Always runs. And it runs before any of the other post conditions.
    // always {
      // Let's wipe out the workspace before we finish!
      // deleteDir()
    // }
    
    success {
      mail(from: "danielsnider12@gmail.com", 
           to: "danielsnider12@gmail.com", 
           subject: "That build passed.",
           body: "Nothing to see here")
    }

    failure {
      mail(from: "danielsnider12@gmail.com", 
           to: "danielsnider12@gmail.com", 
           subject: "That build failed!", 
           body: "Nothing to see here")
    }
  }

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

