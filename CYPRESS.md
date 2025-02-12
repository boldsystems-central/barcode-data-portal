# Running Cypress Tests

This guide explains how to set up and run Cypress tests. If you have already set up the local application or want to test the live version, you can skip the setup section and proceed directly to the instructions for running tests.

---

## 1. Setup (Local Environment)

### Prerequisites
Before proceeding, ensure the following are installed on your machine:
- **Node.js**: If not installed, download and install it from [Node.js](https://nodejs.org/).
- **Tilt**: If using Tilt to manage your application, install it from [Tilt Documentation](https://docs.tilt.dev/install.html).

### Steps for Setup
If you haven’t set up the local environment yet, follow these steps:

1. **Run the Application**
   Start the main application. If using Tilt, navigate to the root of the project and run:
   ```sh
   tilt up -f docker/Tiltfile
   ```

   Open Tilt's dashboard at `http://localhost:10350` and verify that the `fastapi-app` service is running.

2. **Install Cypress Dependencies**
   Navigate to the Cypress directory and install the necessary dependencies:
   ```sh
   cd src/cypress/
   npm install
   ```

3. **Set the Base URL**
   Update the `baseUrl` in your `cypress.config.js` file to point to the application endpoint. For example:
   ```javascript
   module.exports = {
       baseUrl: 'http://localhost:8000', // Change this to match your application or live server URL
   };
   ```

---

## 2. Running Cypress Tests

### Steps to Run Tests

1. **Verify Base URL**
   Ensure the `baseUrl` in your `cypress.config.js` is correct and points to the running application or live server.

2. **Run a Specific Test File**
   To run a single test file, specify the path to the test file:
   ```sh
   npx cypress run --config-file cypress.config.js --spec PATH_TO_TEST/test.cy.js
   ```

3. **Run All Tests**
   To run all test files:
   ```sh
   npx cypress run --config-file cypress.config.js
   ```

---

## Notes
- If you're testing against a live version of the application, skip the setup section and ensure the `baseUrl` in `cypress.config.js` points to the live server.