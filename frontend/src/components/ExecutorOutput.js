import React from 'react';

function ExecutorOutput({ response }) {
  const { result, success, message } = response;

  return (
    <div>
      <h2>Generated Executor Files</h2>
      {success ? (
        <div>
          {Object.entries(result).map(([filename, content]) => (
            <div key={filename}>
              <h3>{filename}</h3>
              <pre>
                <code>{content}</code>
              </pre>
            </div>
          ))}
        </div>
      ) : (
        <div>
          <h3>Error</h3>
          <p>{message}</p>
        </div>
      )}
    </div>
  );
}

export default ExecutorOutput;
