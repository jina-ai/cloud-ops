# Running jina demo on kubernetes

## Deploy jina demo to the cluster in default namespace and use port-forward to access the GUI

- kubectl apply -f https://raw.githubusercontent.com/longwuyuan/cloud-ops/master/kubernetes/manifests/jina-k8s.yaml

- kubectl port-forward service/jina-k8s 12345:12345

- In your browser, open the URL http://localhost:12345

## For exposing jina outside the cluster, with ingress or "k8s-service: --type Loadbalancer"
- Here is a example manifest for kubernetes resource of type Ingress. If you are using a ingress-controller, then you can use this example and modify the host spec, to create a ingress for this jina-demo

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    kubernetes.io/ingress.class: nginx
  name: jina-k8s
spec:
  rules:
  - host: jina-k8s.dev.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: jina-k8s
            port:
              number: 12345
```

Alternatively, if you have the Loadbalancer capability in your kubernetes cluster (using AWS/GCE/Other LB or Metallb), you can use the command `kubectl -n jina expose deployment jina-k8s --type LoadBalancer --port 80 --target-port 12345 --name jina` 

### TODO - Put nginx in front of gunicorn
### TODO - Add kubectl kustomize support
### TODO - Get with making the image official
### TODO - Create operator and any other CRDs needed 
