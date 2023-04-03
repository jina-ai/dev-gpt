

[![Watch the video](https://i.imgur.com/vKb2F1B.png)](https://user-images.githubusercontent.com/11627845/226220484-17810f7c-b184-4a03-9af2-3a977fbb014b.mov)


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
- the code to run requests

# 🤏 limitations for now
- stateless microservices only
- deterministic microservices only to make sure input and output pairs can be used

# TODO:
- [ ] attach playground
- [ ] subtask executors
- 