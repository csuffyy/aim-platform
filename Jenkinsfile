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


showChangeLogs()

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
    HOST_IP = '${InetAddress.localHost.hostAddress}'
  }
  stages {
    stage('Start') {
      steps {
        echo "${params.Greeting} World! ${env.HOST_IP}"
      }
    }
    // stage('Create VM') {
    //     steps {
    //         sh 'touch /home/ubuntu/test'
    //     }
    // }
    stage('ElasticSearch') {
      steps {
        dir('image-archive/elastic-search/') {
          sh 'sudo docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -v `pwd`/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml docker.elastic.co/elasticsearch/elasticsearch:6.6.0'
          sh """bash -c 'while [[ "`curl -v -s -o /dev/null -w ''%{http_code}'' localhost:9200`" != "200" ]]; do echo "trying again"; sleep 5; done'"""
          sh 'docker logs elasticsearch'
          sh 'init_elastic.sh'
          // sh 'sudo docker run -p 1358:1358 -d appbaseio/dejavu'
        }
      }
      post {
        failure {
            sh 'docker rm -f elasticsearch'
        }
      }
    }
  }
}



