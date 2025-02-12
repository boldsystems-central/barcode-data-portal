const { defineConfig } = require("cypress");
const { downloadFile } = require('cypress-downloadfile/lib/addPlugin')

const fs = require('fs');
const path = require('path');

module.exports = defineConfig({
  e2e: {
    screenshotsFolder: '/tmp/cypress/screenshot/',
    downloadsFolder: '/tmp/cypress/downloads/',
    benchmarkFolder: '/tmp/cypress',
    setupNodeEvents(on, config) {
      const resultTsvPath = '/tmp/cypress/results.tsv';
      const benchmarkFolder = '/tmp/cypress';
      on('before:run', () => {
        // Create benchmarkFolder if not exist
        if (!fs.existsSync(benchmarkFolder)) {
          fs.mkdirSync(benchmarkFolder, { recursive: true });
        }
        // Remove previous result
        if (fs.existsSync(resultTsvPath)) {
          fs.writeFileSync(resultTsvPath, '');
        }
      });
      on('task',{
        downloadFile,
        createFolderIfNotExists(folderPath) {
          if (!fs.existsSync(folderPath)) {
            fs.mkdirSync(folderPath, { recursive: true });
          }
          return null;
        },
        getFileSize(filePath) {
          return new Promise((resolve, reject) => {
            fs.stat(filePath, (err, stats) => {
              if (err) {
                return reject(err);
              }
              resolve(stats.size);
            });
          });
        },
        log(message) {
          const logFilePath = path.join(benchmarkFolder, 'test.log');
          const logMessage = `${new Date().toISOString()} - ${message}\n`;
          fs.mkdirSync(path.dirname(logFilePath), { recursive: true });
          fs.appendFileSync(logFilePath, logMessage, { encoding: 'utf8' });
          return null; 
        }
      });
      on('after:spec', (spec, results) => {
        const header = 'Status\tTestName\tDisplay Error';
        const data = results.tests.map(test => `${test.state}\t${test.title.join(' > ')}\t${test.state === 'failed' ? JSON.stringify(test.displayError) : ''}`).join('\n');

        if (!fs.existsSync(resultTsvPath) || fs.readFileSync(resultTsvPath, 'utf8').trim() === '') {
          fs.writeFileSync(resultTsvPath, `${header}\n${data}`);
        } else {
          fs.appendFileSync(resultTsvPath, `\n${data}`);
        }
      });
      return require('./cypress/plugins/index.js')(on, config)
    },
    baseUrl: 'http://localhost',
    // baseUrl: 'https://portal.boldsystems.org',
  },
});
