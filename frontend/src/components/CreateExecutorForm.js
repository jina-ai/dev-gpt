import React, { useState } from 'react';

function CreateExecutorForm({ onCreateExecutor }) {
  const [formData, setFormData] = useState({
    executor_name: '',
    executor_description: '',
    input_modality: '',
    input_doc_field: '',
    output_modality: '',
    output_doc_field: '',
    test_in: '',
    test_out: '',
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreateExecutor(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Executor Name:
        <input
          type="text"
          name="executor_name"
          value={formData.executor_name}
          onChange={handleChange}
          required
        />
      </label>
      <label>
        Input Executor Description:
        <input
          type="text"
          name="executor_description"
          value={formData.executor_description}
          onChange={handleChange}
          required
        />
      </label>
      <label>
        Input Modality:
        <input
          type="text"
          name="input_modality"
          value={formData.input_modality}
          onChange={handleChange}
          required
        />
      </label>
      <label>
        Input Doc Field:
        <input
          type="text"
          name="input_doc_field"
          value={formData.input_doc_field}
          onChange={handleChange}
          required
        />
      </label>
      <label>
        Output Modality:
        <input
          type="text"
          name="output_modality"
          value={formData.output_modality}
          onChange={handleChange}
          required
        />
      </label>
      <label>
        Output Doc Field:
        <input
          type="text"
          name="output_doc_field"
          value={formData.output_doc_field}
          onChange={handleChange}
          required
        />
      </label>
      <label>
        Input Test URL:
        <input
          type="url"
          name="test_in"
          value={formData.test_in}
          onChange={handleChange}
          required
        />
      </label>
      <label>
        Input Test Output:
        <input
          type="text"
          name="test_out"
          value={formData.test_out}
          onChange={handleChange}
          required
        />
      </label>
      <button type="submit">Create Executor</button>
    </form>
  );
}

export default CreateExecutorForm
