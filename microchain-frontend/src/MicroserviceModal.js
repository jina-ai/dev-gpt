import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@material-ui/core';

const modalities = ['image', 'audio', 'text', 'video', '3d'];

const MicroserviceModal = ({ open, onClose, onSave, microservice }) => {
  const [name, setName] = useState(microservice ? microservice.name : '');
  const [input, setInput] = useState(microservice ? microservice.input : '');
  const [output, setOutput] = useState(microservice ? microservice.output : '');

  const handleSubmit = () => {
    onSave({ name, input, output });
    setName('');
    setInput('');
    setOutput('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{microservice ? 'Edit' : 'Add'} Microservice</DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          margin="dense"
          label="Name"
          fullWidth
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <FormControl fullWidth margin="dense">
          <InputLabel id="input-label">Input</InputLabel>
          <Select
            labelId="input-label"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          >
            {modalities.map((modality) => (
              <MenuItem key={modality} value={modality}>
                {modality}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl fullWidth margin="dense">
          <InputLabel id="output-label">Output</InputLabel>
          <Select
            labelId="output-label"
            value={output}
            onChange={(e) => setOutput(e.target.value)}
          >
            {modalities.map((modality) => (
              <MenuItem key={modality} value={modality}>
                {modality}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Cancel
        </Button>
        <Button onClick={handleSubmit} color="primary">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MicroserviceModal;
