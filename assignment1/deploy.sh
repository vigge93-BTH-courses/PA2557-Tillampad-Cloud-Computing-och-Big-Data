CYAN='\033[1;36m'
NC='\033[0m' # No Color

NUM_SHARDS=2

echo -e "${CYAN}Starting RabbitMQ...${NC}"
kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"
kubectl apply -f assignment1.yml -l app=c-message-q

echo -e "${CYAN}Generating webserver secret key...${NC}"
kubectl delete secret cwebserver-secret-key --ignore-not-found
key=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 24)
kubectl create secret generic cwebserver-secret-key --from-literal=secret-key="${key}"

echo -e "${CYAN}Creating shard deploy templates...${NC}"
mkdir tmp
for ((shrd=1; shrd<=$NUM_SHARDS; shrd++)) do
    sed "s/<num>/$shrd/g" shard-template.yml > tmp/shard-$shrd.yml
    kubectl apply -f tmp/shard-$shrd.yml
done


echo -e "${CYAN}Starting communitydb and postdb-manager...${NC}"
kubectl apply -f assignment1.yml -l app=communitydb
kubectl apply -f assignment1.yml -l app=postdb-manager

echo -e "${CYAN}Waiting for communitydb rollout to finish...${NC}"
kubectl rollout status statefulset communitydb

echo -e "${CYAN}Initiating communitydb replicaset...${NC}"
community_initcommand='rs.initiate({_id: "CommunityRepSet", members: [
     { _id: 0, host: "communitydb-0.communitydb-service:27017" },
     { _id: 1, host: "communitydb-1.communitydb-service:27017" },
     { _id: 2, host: "communitydb-2.communitydb-service:27017" },
]});'
kubectl exec -i communitydb-0 -- mongosh --quiet --eval "$community_initcommand"


for ((shrd=1; shrd<=$NUM_SHARDS; shrd++)) do
    echo -e "${CYAN}Waiting for shard $shrd rollout to finish...${NC}"
    kubectl rollout status statefulset postdb-shrd-$shrd
    echo -e "${CYAN}Initiating shard $shrd replicaset...${NC}"
    shard_initcommand="rs.initiate({_id: \"postShrd${shrd}RepSet\", members: [
        { _id: 0, host: \"postdb-shrd-${shrd}-0.postdb-shrd-${shrd}-service:27018\" },
        { _id: 1, host: \"postdb-shrd-${shrd}-1.postdb-shrd-${shrd}-service:27018\" },
        { _id: 2, host: \"postdb-shrd-${shrd}-2.postdb-shrd-${shrd}-service:27018\" },
    ]});"
    kubectl exec -i postdb-shrd-$shrd-0 -- mongosh --port 27018 --quiet --eval "$shard_initcommand"
done

echo -e "${CYAN}Waiting for postdb-manager rollout to finish...${NC}"
kubectl rollout status statefulset postdb-manager

echo -e "${CYAN}Initiating communitydb replicaset...${NC}"
postMan_initcommand='rs.initiate({_id: "postManRepSet", configsvr: true, members: [
     { _id: 0, host: "postdb-manager-0.postdb-manager-service:27019" },
     { _id: 1, host: "postdb-manager-1.postdb-manager-service:27019" },
     { _id: 2, host: "postdb-manager-2.postdb-manager-service:27019" },
]});'
kubectl exec -i postdb-manager-0 -- mongosh --port 27019 --quiet --eval "$postMan_initcommand"

echo -e "${CYAN}Starting mongos for sharding and waiting for rollout to finish...${NC}"
kubectl apply -f assignment1.yml -l app=postdb-mongos
kubectl rollout status statefulset postdb-mongos

echo -e "${CYAN}Adding shards to mongos...${NC}"
for ((shrd=1; shrd<=$NUM_SHARDS; shrd++)) do
    kubectl exec -i postdb-mongos-0 -- mongosh --quiet --eval "sh.addShard(
        \"postShrd${shrd}RepSet/postdb-shrd-${shrd}-0.postdb-shrd-${shrd}-service:27018,postdb-shrd-${shrd}-1.postdb-shrd-${shrd}-service:27018,postdb-shrd-${shrd}-2.postdb-shrd-${shrd}-service:27018\")"
done

echo -e "${CYAN}Sharding posts collection...${NC}"
kubectl exec -i postdb-mongos-0 -- mongosh --quiet --eval 'sh.shardCollection("PostDB.posts", {community_id: "hashed"})'

echo -e "${CYAN}Waiting for RabbitMQ to finish rollout...${NC}"
kubectl rollout status statefulset c-message-q-server

echo -e "${CYAN}Deploying other services...${NC}"
kubectl apply -f assignment1.yml

echo -e "${CYAN}Waiting for web server rollout to finish...${NC}"
kubectl rollout status deployment cwebserver

echo -e "${CYAN}Deployment done!${NC}"