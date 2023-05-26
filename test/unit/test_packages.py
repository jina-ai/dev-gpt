from dev_gpt.options.generate.generator import Generator

def test_package_parsing():
    packages_json_string = '''\
    [
      ["PyPDF2", "gpt_3_5_turbo"],
      ["pdfminer.six", "gpt_3_5_turbo"],
      ["tika", "gpt_3_5_turbo"],
      [],
      ["gpt_3_5_turbo"]
    ]'''

    parsed_packages = Generator.process_packages_json_string(packages_json_string)
    for parsed, expected in zip(parsed_packages, [
        ['pypdf2', 'gpt_3_5_turbo'],
        ['pdfminer.six', 'gpt_3_5_turbo'],
        [],
        ['gpt_3_5_turbo'],
    ]):
        assert set(parsed) == set(expected)