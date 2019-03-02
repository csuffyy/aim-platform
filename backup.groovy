def changeLogSets = currentBuild.changeSets
for (int i = 0; i < changeLogSets.size(); i++) {
  def entries = changeLogSets[i].items
  for (int j = 0; j < entries.length; j++) {
    def entry = entries[j]
    def files = new ArrayList(entry.affectedFiles)
    for (int k = 0; k < files.size(); k++) {
      def file = files[k]
      println file.path
    }
  }
}


pipeline {
  agent {
    label "development"
  }
  parameters {
    string(name: 'Greeting', defaultValue: 'Hello', description: 'How should I greet the world?')
  }
  environment {
    CI = 'true'
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
      dir('image-archive/elastic-search/') {
        steps {
          sh 'sudo docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" -v elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml docker.elastic.co/elasticsearch/elasticsearch:6.6.0'
          sh 'init_elastic.sh'
          // sh 'sudo docker run -p 1358:1358 -d appbaseio/dejavu'
        }
      }
    }
    stage('DWV') {
      dir('image-archive/dwv/') {
        steps {
          sh 'yarn install'
          sh 'yarn run start'
        }
      }
    }
    stage('ReactiveSearch') {
      dir('image-archive/reactive-search/') {
        steps {
          sh 'npm install'
          sh 'npm run dev'
        }
      }
    }
    // stage('Deliver for development') {
    //   when {
    //     branch 'development'
    //   }
    //   steps {
    //     sh 'echo helloworld'
    //     input message: 'Finished using the web site? (Click "Proceed" to continue)'
    //     sh 'echo kill-server'
    //   }
    // }
  }

  post {
    // Always runs. And it runs before any of the other post conditions.
    always {
      // Let's wipe out the workspace before we finish!
      // deleteDir()
    }
    
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









