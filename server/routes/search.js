const express = require('express');
const router = express.Router();
const searchService = require('../services/search');

router.get('/search', (req, res) => {
    const query = req.query.q;
    const results = searchService(query);

    res.json({ results });
});

module.exports = router;