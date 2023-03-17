import React from 'react';
import { Card, CardContent, Typography } from '@material-ui/core';

const Microservice = ({ microservice }) => {
  return (
    <Card>
      <CardContent>
        <Typography variant="h6">{microservice.name}</Typography>
        <Typography>
          Input: {microservice.input} | Output: {microservice.output}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default Microservice;