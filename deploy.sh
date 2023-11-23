kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"
kubectl apply -f assignment1.yml -l app=c-message-q
sleep 1
kubectl rollout status statefulset c-message-q-server

kubectl delete secret cwebserver-secret-key --ignore-not-found
kubectl create secret generic cwebserver-secret-key --from-literal=secret-key='123'

kubectl apply -f assignment1.yml