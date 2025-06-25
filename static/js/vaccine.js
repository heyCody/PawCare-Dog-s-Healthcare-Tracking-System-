document.addEventListener('DOMContentLoaded', async () => {
            const dogNameElem = document.getElementById('dogName');
            const dogDOBElem = document.getElementById('dogDOB');
            const scheduleTableBody = document.getElementById('scheduleTableBody');
            const historyTableBody = document.getElementById('historyTableBody');

            // Function to display an error message in the dashboard sections
            const displayError = (message) => {
                dogNameElem.textContent = 'Error loading data.';
                dogDOBElem.textContent = '';
                scheduleTableBody.innerHTML = `<tr><td colspan="3" class="text-center py-4 text-red-500">${message}</td></tr>`;
                historyTableBody.innerHTML = `<tr><td colspan="2" class="text-center py-4 text-red-500">${message}</td></tr>`;
            };

            try {
                // Fetch dog vaccine data from the Flask backend API
                // In a real application, you might pass a dog_id as a query parameter or from a user session
                const response = await fetch('/api/dog_vaccine_data'); 
                
                // Check if the HTTP response was successful
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                // Parse the JSON response from the backend
                const data = await response.json();

                // Populate Dog Information section
                dogNameElem.textContent = data.dog_name || 'N/A';
                dogDOBElem.textContent = data.dog_dob || 'N/A';

                // Populate Upcoming Vaccine Schedule table
                scheduleTableBody.innerHTML = ''; // Clear existing loading message
                if (data.schedule && data.schedule.length > 0) {
                    // Iterate over each schedule item and append a row to the table
                    data.schedule.forEach(item => {
                        const row = `
                            <tr>
                                <td class="whitespace-nowrap">${item.vaccine || 'N/A'}</td>
                                <td class="whitespace-nowrap">${item.due_date || 'N/A'}</td>
                                <td>${item.notes || 'No notes'}</td>
                            </tr>
                        `;
                        scheduleTableBody.insertAdjacentHTML('beforeend', row);
                    });
                } else {
                    // Display a message if no upcoming vaccines are found
                    scheduleTableBody.innerHTML = `<tr><td colspan="3" class="text-center py-4 text-gray-500">No upcoming vaccines.</td></tr>`;
                }

                // Populate Vaccination History table
                historyTableBody.innerHTML = ''; // Clear existing loading message
                if (data.history && data.history.length > 0) {
                    // Iterate over each history item and append a row to the table
                    data.history.forEach(item => {
                        const row = `
                            <tr>
                                <td class="whitespace-nowrap">${item.vaccine || 'N/A'}</td>
                                <td class="whitespace-nowrap">${item.date_given || 'N/A'}</td>
                            </tr>
                        `;
                        historyTableBody.insertAdjacentHTML('beforeend', row);
                    });
                } else {
                    // Display a message if no vaccination history is found
                    historyTableBody.innerHTML = `<tr><td colspan="2" class="text-center py-4 text-gray-500">No vaccination history recorded.</td></tr>`;
                }

            } catch (error) {
                // Log and display any errors during data fetching
                console.error('Failed to fetch dog vaccine data:', error);
                displayError('Failed to load vaccine data. Please try again later.');
            }
        });
        