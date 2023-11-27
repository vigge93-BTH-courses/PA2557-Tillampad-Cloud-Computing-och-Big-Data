# Start queue related services
kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"
kubectl apply -f assignment1.yml -l app=c-message-q

# Generate secret key for cwebserver
kubectl delete secret cwebserver-secret-key --ignore-not-found
kubectl create secret generic cwebserver-secret-key --from-literal=secret-key='123'

# Start database services
kubectl apply -f assignment1.yml -l app=communitydb
kubectl apply -f assignment1.yml -l app=postdb-manager
kubectl apply -f assignment1.yml -l app=postdb-shrd-1
kubectl apply -f assignment1.yml -l app=postdb-shrd-2

# Configure CommunityDB
kubectl rollout status statefulset communitydb

community_initcommand='rs.initiate({_id: "CommunityRepSet", members: [
     { _id: 0, host: "communitydb-0.communitydb-service:27017" },
     { _id: 1, host: "communitydb-1.communitydb-service:27017" },
     { _id: 2, host: "communitydb-2.communitydb-service:27017" },
]});'
kubectl exec -i communitydb-0 -- mongosh --quiet --eval "$community_initcommand"

initwait="while('PRIMARY' != rs.status()['members'][0]['stateStr']) { sleep(1000); console.log('Waiting to become PRIMARY...'); }"

# Configure PostDB sharded cluster
kubectl rollout status statefulset postdb-manager
kubectl rollout status statefulset postdb-shrd-1
kubectl rollout status statefulset postdb-shrd-2

postMan_initcommand='rs.initiate({_id: "postManRepSet", configsvr: true, members: [
     { _id: 0, host: "postdb-manager-0.postdb-manager-service:27019" },
     { _id: 1, host: "postdb-manager-1.postdb-manager-service:27019" },
     { _id: 2, host: "postdb-manager-2.postdb-manager-service:27019" },
]});'
shard1_initcommand='rs.initiate({_id: "postShrd1RepSet", members: [
     { _id: 0, host: "postdb-shrd-1-0.postdb-shrd-1-service:27018" },
     { _id: 1, host: "postdb-shrd-1-1.postdb-shrd-1-service:27018" },
     { _id: 2, host: "postdb-shrd-1-2.postdb-shrd-1-service:27018" },
]});'
shard2_initcommand='rs.initiate({_id: "postShrd2RepSet", version: 1, members: [
     { _id: 0, host: "postdb-shrd-2-0.postdb-shrd-2-service:27018" },
     { _id: 1, host: "postdb-shrd-2-1.postdb-shrd-2-service:27018" },
     { _id: 2, host: "postdb-shrd-2-2.postdb-shrd-2-service:27018" },
]});'

kubectl exec -i postdb-manager-0 -- mongosh --port 27019 --quiet --eval "$postMan_initcommand"
kubectl exec -i postdb-shrd-1-0 -- mongosh --port 27018 --quiet --eval "$shard1_initcommand"
kubectl exec -i postdb-shrd-2-0 -- mongosh --port 27018 --quiet --eval "$shard2_initcommand"

# Create and configure mongos for Sharded cluster
kubectl apply -f assignment1.yml -l app=postdb-mongos
kubectl rollout status statefulset postdb-mongos
kubectl exec -i postdb-mongos-0 -- mongosh --quiet --eval 'sh.addShard("postShrd1RepSet/postdb-shrd-1-0.postdb-shrd-1-service:27018,postdb-shrd-1-1.postdb-shrd-1-service:27018,postdb-shrd-1-2.postdb-shrd-1-service:27018")'
kubectl exec -i postdb-mongos-0 -- mongosh --quiet --eval 'sh.addShard("postShrd2RepSet/postdb-shrd-2-0.postdb-shrd-2-service:27018,postdb-shrd-2-1.postdb-shrd-2-service:27018,postdb-shrd-2-2.postdb-shrd-2-service:27018")'
kubectl exec -i postdb-mongos-0 -- mongosh --quiet --eval 'sh.shardCollection("PostDB.posts", {community_id: "hashed"})'

# Make sure that the queue service has started before deploying the rest.
kubectl rollout status statefulset c-message-q-server

# Deploy everyting else and wait for webserver to start
kubectl apply -f assignment1.yml
kubectl rollout status deployment cwebserver