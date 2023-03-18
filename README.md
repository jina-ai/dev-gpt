
# 🔮 vision
create, deploy and update your microservice infrastructure

# 🏗 frontend description 
The microchain-frontend is used to define the graph of microservice, their interfaces and their functionality.
Based on this definition, the backend will be generated automatically.

# 🏗 usage single microservice
## you provide 
- input_modality
- output_modality
- description of the functionality of the transformation the microservice is handling
- examples of input and output pairs

## you get
- a microservice together with a playground

# 🤏 limitations for now
- stateless microservices only
- deterministic microservices only to make sure input and output pairs can be used