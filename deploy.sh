kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"
kubectl apply -f assignment1-rabbitmq.yml
sleep 60 # TODO: Remove
rabbitmq_username="$(kubectl get secret c-message-q-default-user -o jsonpath='{.data.username}' | base64 --decode)"
rabbitmq_password="$(kubectl get secret c-message-q-default-user -o jsonpath='{.data.password}' | base64 --decode)"
rabbitmq_service="$(kubectl get service c-message-q -o jsonpath='{.spec.clusterIP}')"
echo $rabbitmq_username # TODO: Remove?
echo $rabbitmq_password # TODO: Remove?
kubectl create secret generic cwebserver-secret-key --from-literal=secret-key='123'
kubectl apply -f assignment1.yml
kubectl port-forward "service/c-message-q" 5672 # TODO: Remove