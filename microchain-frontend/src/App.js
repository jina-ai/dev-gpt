import React, {useState} from 'react';
import axios from 'axios';
import {Box, Container, FormControl, InputLabel, MenuItem, Select, TextField, Typography,} from '@mui/material';
import copy from 'clipboard-copy';
import Button from '@mui/material/Button';

function App() {
    const [executorName, setExecutorName] = useState('MyCoolOcrExecutor');
    const [executorDescription, setExecutorDescription] = useState('OCR detector');
    const [inputModality, setInputModality] = useState('image');
    const [inputDocField, setInputDocField] = useState('uri');
    const [outputModality, setOutputModality] = useState('text');
    const [outputDocField, setOutputDocField] = useState('text');
    const [testIn, settestIn] = useState('https://miro.medium.com/v2/resize:fit:1024/0*4ty0Adbdg4dsVBo3.png');
    const [testOut, settestOut] = useState('> Hello, world!_');
    const [responseText, setResponseText] = useState(null);


    const handleSubmit = async (e) => {
        e.preventDefault();

        const requestBody = {
            executor_name: executorName,
            executor_description: executorDescription,
            input_modality: inputModality,
            input_doc_field: inputDocField,
            output_modality: outputModality,
            output_doc_field: outputDocField,
            test_in: testIn,
            test_out: testOut,
        };

        try {
            const response = await axios.post('http://0.0.0.0:8000/create', requestBody);
            console.log(response.data)
            setResponseText(response.data);
        } catch (error) {
            console.error(error);
            setResponseText('An error occurred while processing the request.');
        }
    };

    const handleCopy = (fileContent) => {
        copy(fileContent);
    };

    return (
        <Container maxWidth="md">
            <Box sx={{my: 4}}>
                <Typography variant="h4" component="h1" gutterBottom>
                    MicroChain
                </Typography>
                <Typography variant="body1" component="p" gutterBottom>
                    ✨ Magically create your microservice just by describing it.
                </Typography>
                <form onSubmit={handleSubmit}>
                    <Box sx={{my: 2}}>
                        <TextField
                            label="Executor Name"
                            value={executorName}
                            onChange={(e) => setExecutorName(e.target.value)}
                            fullWidth
                        />
                    </Box>
                    <Box sx={{my: 2}}>
                        <TextField
                            label="Executor Description"
                            value={executorDescription}
                            onChange={(e) => setExecutorDescription(e.target.value)}
                            fullWidth
                        />
                    </Box>
                    <Box sx={{my: 2}}>
                        <Typography variant="h6" component="h2" gutterBottom>
                            Input Interface
                        </Typography>
                        <FormControl fullWidth>
                            <InputLabel id="input-modality-label">Input Modality</InputLabel>
                            <Select
                                labelId="input-modality-label"
                                value={inputModality}
                                onChange={(e) => setInputModality(e.target.value)}
                            >
                                <MenuItem value="text">Text</MenuItem>
                                <MenuItem value="image">Image</MenuItem>
                                <MenuItem value="3d">3D</MenuItem>
                                <MenuItem value="audio">Audio</MenuItem>
                                <MenuItem value="video">Video</MenuItem>
                                <MenuItem value="pdf">PDF</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                    <Box sx={{my: 2}}>
                        <FormControl fullWidth>
                            <InputLabel id="input-doc-field-label">Input Doc Field</InputLabel>
                            <Select
                                labelId="input-doc-field-label"
                                value={inputDocField}
                                onChange={(e) => setInputDocField(e.target.value)}
                            >
                                <MenuItem value="text">Text</MenuItem>
                                <MenuItem value="blob">Blob</MenuItem>
                                <MenuItem value="tensor">Tensor</MenuItem>
                                <MenuItem value="uri">URL</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                    <Box sx={{my: 2}}>
                        <Typography variant="h6" component="h2" gutterBottom>
                            Output Interface
                        </Typography>
                        <FormControl fullWidth>
                            <InputLabel id="output-modality-label">Output Modality</InputLabel>
                            <Select
                                labelId="output-modality-label"
                                value={outputModality}
                                onChange={(e) => setOutputModality(e.target.value)}
                            >
                                <MenuItem value="text">Text</MenuItem>
                                <MenuItem value="image">Image</MenuItem>
                                <MenuItem value="3d">3D</MenuItem>
                                <MenuItem value="audio">Audio</MenuItem>
                                <MenuItem value="video">Video</MenuItem>
                                <MenuItem value="pdf">PDF</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                    <Box sx={{my: 2}}>
                        <FormControl fullWidth>
                            <InputLabel id="output-doc-field-label">Output Doc Field</InputLabel>
                            <Select
                                labelId="output-doc-field-label"
                                value={outputDocField}
                                onChange={(e) => setOutputDocField(e.target.value)}
                            >
                                <MenuItem value="text">Text</MenuItem>
                                <MenuItem value="blob">Blob</MenuItem>
                                <MenuItem value="tensor">Tensor</MenuItem>
                                <MenuItem value="uri">URL</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                    <Box sx={{my: 2}}>
                        <Typography variant="h6" component="h2" gutterBottom>
                            Test Parameters
                        </Typography>
                        <TextField
                            label="Input Test In"
                            value={testIn}
                            onChange={(e) => settestIn(e.target.value)}
                            fullWidth
                        />
                    </Box>
                    <Box sx={{my: 2}}>
                        <TextField
                            label="Input Test Out"
                            value={testOut}
                            onChange={(e) => settestOut(e.target.value)}
                            fullWidth
                        />
                    </Box>
                    <Box sx={{my: 2}}>
                        <Button type="submit" variant="contained" color="primary">
                            Submit
                        </Button>
                    </Box>
                </form>
                {responseText && (
                    <Box sx={{my: 4}}>
                        <Typography variant="h6" component="h2" gutterBottom>
                            Response
                        </Typography>
                        {Object.entries(responseText.result).map(([fileName, fileContent]) => (
                            <Box key={fileName} sx={{my: 2, p: 2, border: '1px solid #ddd', borderRadius: '4px'}}>
                                <Typography variant="subtitle1" gutterBottom>
                                    {fileName}
                                </Typography>
                                <pre>{fileContent}</pre>
                                <Button
                                    onClick={() => handleCopy(fileContent)}
                                    variant="outlined"
                                    color="primary"
                                    size="small"
                                >
                                    Copy Code
                                </Button>
                            </Box>
                        ))}
                    </Box>
                )}
            </Box>
        </Container>
    );
}

export default App;
