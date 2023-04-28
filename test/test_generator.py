import os

from src.options.generate.generator import Generator


# The cognitive difficulty level is determined by the number of requirements the microservice has.

def test_generation_level_0(tmpdir):
    """
    Requirements:
    coding: ❌
    pip packages: ❌
    environment: ❌
    GPT-3.5-turbo: ❌
    APIs: ❌
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(
        "The microservice is very simple, it does not take anything as input and only outputs the word 'test'",
        str(tmpdir) + 'microservice',
        'gpt-3.5-turbo'
    )
    generator.generate()


def test_generation_level_1(tmpdir):
    """
    Requirements:
    coding: ❌
    pip packages: ✅ (pdf parser)
    environment: ❌
    GPT-3.5-turbo: ❌
    APIs: ❌
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(
        "The input is a PDF like https://www.africau.edu/images/default/sample.pdf and the output the parsed text",
        str(tmpdir) + 'microservice',
        'gpt-3.5-turbo'
    )
    generator.generate()


def test_generation_level_4(tmpdir):
    """
    Requirements:
    coding: ✅ (putting text on the image)
    pip packages: ✅ (Pillow for image processing)
    environment: ❌
    GPT-3.5-turbo: ✅ (for writing the joke)
    APIs: ✅ (scenex for image description)
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(f'''
The input is an image like this: https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/560px-PNG_transparency_demonstration_1.png.
Use the following api to get the description of the image:
Request:
curl "https://us-central1-causal-diffusion.cloudfunctions.net/describe" \
  -H "x-api-key: token {os.environ['SCENEX_API_KEY']}" \
  -H "content-type: application/json" \
  --data '{{"data":[
  {{"image": "<image url here>", "features": []}}
  ]}}'
Result format:
{
    "result": [
    {
    "text": "<image description>"
    }
  ]
}
The description is then used to generate a joke.
The joke is the put on the image.
The output is the image with the joke on it.''',
                          str(tmpdir) + 'microservice',
                          'gpt-3.5-turbo'
                          )
    generator.generate()
