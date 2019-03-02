def changeLogSets = currentBuild.changeSets
for (int i = 0; i < changeLogSets.size(); i++) {
  def entries = changeLogSets[i].items
  for (int j = 0; j < entries.length; j++) {
    def entry = entries[j]
    def files = new ArrayList(entry.affectedFiles)
    for (int k = 0; k < files.size(); k++) {
      def file = files[k]
      println file.path
      println "file.path"
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
        echo "${params.Greeting} World!"
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
          sh 'sudo docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -v `pwd`/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml docker.elastic.co/elasticsearch/elasticsearch:6.6.0'
          sh 'echo 1-$HOST_IP'
          sh 'init_elastic.sh'
          // sh 'sudo docker run -p 1358:1358 -d appbaseio/dejavu'
        }
      }
    }
  }
}



