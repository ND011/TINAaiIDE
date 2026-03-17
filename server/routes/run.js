const express = require('express');
const router = express.Router();
const { exec } = require('child_process');

// Whitelisted commands
const allowedCommands = ['python', 'node'];

router.post('/run/start', (req, res) => {
    const { command, args } = req.body;

    if (!allowedCommands.includes(command)) {
        return res.status(403).json({ error: 'Command not allowed' });
    }

    const childProcess = exec(`${command} ${args.join(' ')}`, (error, stdout, stderr) => {
        if (error) {
            res.status(500).json({ error: error.message });
        } else {
            res.json({ stdout, stderr });
        }
    });

    childProcess.stdout.on('data', (data) => {
        // Handle stdout
    });

    childProcess.stderr.on('data', (data) => {
        // Handle stderr
    });
});

router.post('/run/stop', (req, res) => {
    const { runId } = req.body;

    // Logic to stop the process based on runId

    res.status(200).json({ message: 'Process stopped' });
});

router.get('/run/:id/status', (req, res) => {
    const { id } = req.params;

    // Logic to get the status of the process

    res.json({ status: 'running' });
});

module.exports = router;