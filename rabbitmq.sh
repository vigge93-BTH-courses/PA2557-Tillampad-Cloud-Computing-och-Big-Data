username="$(kubectl get secret c-message-q-default-user -o jsonpath='{.data.username}' | base64 --decode)"
echo "username: $username"
password="$(kubectl get secret c-message-q-default-user -o jsonpath='{.data.password}' | base64 --decode)"
echo "password: $password"

kubectl port-forward "service/c-message-q" 15672