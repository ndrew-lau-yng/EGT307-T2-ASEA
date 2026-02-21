# EGT307-T2-ASEA
Kubernetes App Depolyment for predictive maintenance of machine failure. 

Done by Andrew, Srishti, Elisha and Amirul.

## Project Overview and Objectives

The project implements a predictive maintenance system for machine failure using a microservices architecture deployed on Kubernetes. The primary objective is to predict potential machine failures based on sensor data, enabling proactive maintenance and reducing downtime. The system comprises a frontend for user interaction, an API gateway for request orchestration, an inference service for machine learning predictions, and a PostgreSQL database for logging and persistence.

## Instructions to build, run, and deploy the system (Docker & Kubernetes)

1. Download our project folder and unzip it.

2. Have Docker Desktop open with the engine running before continuing

3. Open powershell and navigate to the project folder directory (.\EGT307-T2-ASEA)

4. Start Minikube: 
    minikube start

5. Enable these addons:
    minikube addons enable ingress
    minikube addons enable metrics-server

6. Create the namespace:
    kubectl create namespace egt307

7. Apply the yaml files:
    kubectl apply -f .\k8s\database-service\ -n egt307
    kubectl apply -f .\k8s\inference-service\ -n egt307
    kubectl apply -f .\k8s\api-gateway-service\ -n egt307
    kubectl apply -f .\k8s\frontend-service\ -n egt307
    kubectl apply -f .\k8s\ingress\ingress.yaml -n egt307

8. Wait until all pods are stable and running (status=running & ready=1/1 etc):
    kubectl get pods -n egt307

9. Start the ingress access (*Use the first link address only*):
    minikube service ingress-nginx-controller -n ingress-nginx --url
    Something like this should output:
        http://127.0.0.1:63704
        http://127.0.0.1:63705
    We will use the first one.

10. Now you can freely access the system by ctrl+click or copying the address to a browser:
    http://127.0.0.1:63704     #Change port accordingly

13. Once finish, stop Minikube:
    minikube stop

Additional Info to verify components:

To check API Health in browser:
    http://<IP>:<port>/api/health

To check HPA in Powershell:
    kubectl get hpa -n egt307

To check metrics in Powershell:

    kubectl top pods -n egt307

        

## Description of each microservice and its purpose

**1. Frontend Service (Streamlit)**

This service provides the user interface for interacting with the predictive maintenance system. Users can input sensor data through a web form, which is then sent to the API Gateway for processing. The frontend displays the prediction results, indicating whether a machine failure is likely.

**2. API Gateway Service (FastAPI)**

Serving as the central entry point for all API requests, the API Gateway orchestrates the flow of data between the frontend, inference service, and database. It receives sensor data from the frontend, forwards it to the inference service for prediction, and then logs both the input data and the prediction results into the PostgreSQL database. Additionally, it records request metadata such as latency and status codes for monitoring and auditing purposes.

**3. Inference Service (FastAPI)**

The Inference Service is responsible for hosting and executing the machine learning model. It receives sensor data from the API Gateway, processes it using the pre-trained model, and returns a prediction (failure or no failure) along with the probability of failure. The model is a RandomForestClassifier trained on historical machine data.

**4. Database Service (PostgreSQL)**

This service provides persistent storage for the system. It stores all prediction requests, their corresponding input data, and the generated prediction results. It also maintains a log of API requests, including routes, status codes, and latencies, which can be used for performance analysis and debugging.

## Dataset information and sources

AI4I 2020 Predictive Maintenance Dataset

https://www.kaggle.com/competitions/playground-series-s3e17/data

| Variable Name | Role | Type | Units |
| :- | :- | :- | :- |
| **ID** | ID | Integer | - |
| **Product ID** | ID | Categorical | - |
| **Type** | Feature | Categorical | - |
| **Air Temperature** | Feature | Continuous | K |
| **Process Temperature** | Feature | Continuous | K |
| **Rotational speed** | Feature | Integer | rpm |
| **Torque**| Feature | Continuous | Nm
|**Tool Wear**| Feature | Integer | min
|**Machine Failure**| Target | Integer | - |
|**TWF**| Target | Integer | - |
|**HDF**| Target | Integer | - |
|**PWF**| Target | Integer | - |
|**OSF**| Target | Integer | - |
|**RNF**| Target | Integer | - |

## Reference for the ML Model

The creation of the trained model was done by following the notebook below:

Jeevika Sharma's ML-Powered Maintenance: Smarter & Proactive

https://www.kaggle.com/code/jeevikasharma2003/ml-powered-maintenance-smarter-proactive


## Any known issues or limitations

The main issue faced was the integration of the different microservices, during the Docker Containerization stage, the Kubernetes Implementation stage and the Ingress Addon stage. As everyone worked on their own services individually, it meant that each person configured their files using different ports, url links and requirements.