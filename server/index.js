const express = require('express');
const bodyParser = require('body-parser');
const app = express();
const port = 3000;

app.use(bodyParser.json());

// Other routes and middleware

const searchRoutes = require('./routes/search');
app.use('/search', searchRoutes);

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});