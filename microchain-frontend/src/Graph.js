import React, { useState } from 'react';
import Microservice from './Microservice';
import MicroserviceModal from './MicroserviceModal';
import { Button, Grid } from '@material-ui/core';

const Graph = ({ onExport }) => {
  const [microservices, setMicroservices] = useState([]);
  const [selectedMicroservice, setSelectedMicroservice] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const handleSave = (microservice) => {
    if (selectedMicroservice) {
      setMicroservices(
        microservices.map((ms) =>
          ms.id === selectedMicroservice.id ? microservice : ms
        )
      );
    } else {
      setMicroservices([...microservices, { ...microservice, id: Date.now() }]);
    }
    setSelectedMicroservice(null);
  };

  const handleEdit = (microservice) => {
    setSelectedMicroservice(microservice);
    setShowModal(true);
  };

  return (
    <div>
      <Button onClick={() => setShowModal(true)}>Add Microservice</Button>
      <Button onClick={() => onExport(microservices)}>Export Graph</Button>
      <Grid container spacing={2}>
        {microservices.map((microservice) => (
          <Grid key={microservice.id} item xs={12} sm={6} md={4}>
            <div onClick={() => handleEdit(microservice)}>
              <Microservice microservice={microservice} />
            </div>
          </Grid>
        ))}
      </Grid>
      <MicroserviceModal
        open={showModal}
        onClose={() => setShowModal(false)}
        onSave={handleSave}
        microservice={selectedMicroservice}
      />
    </div>
  );
};

export default Graph;
