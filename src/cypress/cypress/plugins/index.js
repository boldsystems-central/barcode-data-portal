// cypress/plugins/index.js
let setupPlugin = require('cypress-benchmark/plugin')

module.exports = (on, config) => {
    setupPlugin(on)
}
