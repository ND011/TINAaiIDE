const fs = require('fs');
const path = require('path');

function searchDirectory(directory) {
    let results = [];

    fs.readdirSync(directory).forEach(file => {
        const fullPath = path.join(directory, file);
        if (fs.lstatSync(fullPath).isDirectory()) {
            results = results.concat(searchDirectory(fullPath));
        } else {
            results.push(fullPath);
        }
    });

    return results;
}

module.exports = searchDirectory;