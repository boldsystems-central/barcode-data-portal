describe('User Journey Test - Title', () => {
    it('Explain the user journey here', () => {
        // start with visiting a page. usually the index page
        cy.visit('/');

        // Only if you need to the test the page after $(document).ready is finished you need to wait, otherwise you don't need to wait
        cy.wait(500)

        // You can select everything you want using
        // In this case a <p> tag with "fungal-and-other-species" is selected
        cy.get('p#fungal-and-other-species')
        .invoke('text')
        .then((text) => {
            // You can process the text inside the <p> tag here
            // At first we convert it to int
            const number = parseInt(text.trim(), 10);
            // Now we make sure that it is bigger than 0
            expect(number).to.be.greaterThan(0);
        });

        // We can write in the search bar
        // In this case we write Canada in the search bar
        cy.get('#query').type('Canada');

        // From the dropdown list we select Canada[geo]
        cy.get('.dropdown-item')
        .contains('Canada[geo]')
        .click();

        // Click on the search button
        cy.get('button')
        .contains('Search')
        .click();

        // Make sure that the new url contains query=Canada[geo]
        // Currently the url is /result?query=Canada[geo]
        cy.url().should('include', 'query=Canada[geo]');
    });
});