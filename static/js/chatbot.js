const symptoms = [
    "fever","vomiting","paralysis","reduced appetite","coughing","discharge from eyes","hyper keratosis",
    "nasal discharge","lethargy","sneezing","diarrhea","depression","difficulty in breathing","pain",
    "skinsores","inflammation eyes","anorexia","seizures","dehydration","weight loss","bloody stool",
    "weakness","inflammation mouth","rapid heartbeat","fatigue","swollen belly","laziness","anemia",
    "fainting","reverse sneezing","gagging","lameness","stiffness","limping","increased thirst",
    "increased urination","excess salivation","aggression","foaming at mouth","difficulty in swallowing",
    "irritable","pica","hydrophobia","highly excitable","shivering","jaundice","decreased thirst",
    "decreased urination","blood in urine","palegums","ulcers in mouth","bad breath"
];

const conditionDisplayNames = {
    "rabies": "Rabies",
    "caninedistemper": "Canine Distemper",
    "leptospirosis": "Leptospirosis",
    "kidneydisease": "Kidney Disease",
    "kennelcough": "Kennel Cough",
    "heartworm": "Heartworm",
    "canineparvovirus": "Canine Parvovirus"
};

function getDisplayName(conditionCode) {
    return conditionDisplayNames[conditionCode.toLowerCase()] || conditionCode;
}

const selectedSymptoms = [];
const chatbox = document.getElementById('chatbox');
const fileInput = document.getElementById('file-input');
let optionsShown = false;

function botTypingMessage(finalText, delay = 1000, callback = null) {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot typing';
    typingDiv.textContent = 'Typing';
    chatbox.appendChild(typingDiv);
    chatbox.scrollTop = chatbox.scrollHeight;

    setTimeout(() => {
        typingDiv.remove();
        const botMsg = document.createElement('div');
        botMsg.className = 'message bot';
        botMsg.textContent = finalText;
        chatbox.appendChild(botMsg);
        chatbox.scrollTop = chatbox.scrollHeight;
        if (callback) callback();
    }, delay);
}

function showInitialOptions() {
    if (!optionsShown) {
        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'message';
        
        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'options-group';

        const symptomsBtn = document.createElement('button');
        symptomsBtn.className = 'option-btn';
        symptomsBtn.textContent = 'Select Symptoms';
        symptomsBtn.onclick = () => {
            optionsShown = true;
            showSymptomOptions();
            buttonGroup.remove();
        };

        const uploadBtn = document.createElement('button');
        uploadBtn.className = 'option-btn';
        uploadBtn.textContent = 'Upload Picture';
        uploadBtn.onclick = () => {
            optionsShown = true;
            fileInput.click();
            buttonGroup.remove();
        };

        buttonGroup.appendChild(symptomsBtn);
        buttonGroup.appendChild(uploadBtn);
        optionsContainer.appendChild(buttonGroup);
        chatbox.appendChild(optionsContainer);
        chatbox.scrollTop = chatbox.scrollHeight;
    }
}

function showSymptomOptions() {
    const optionsContainer = document.createElement('div');
    optionsContainer.className = 'message';

    const list = document.createElement('ul');
    list.className = 'symptom-list';

    symptoms.forEach(symptom => {
        const li = document.createElement('li');
        li.textContent = symptom;
        li.className = 'symptom-item';
        li.onclick = () => {
            if (selectedSymptoms.includes(symptom)) {
                selectedSymptoms.splice(selectedSymptoms.indexOf(symptom), 1);
                li.classList.remove('selected');
            } else {
                selectedSymptoms.push(symptom);
                li.classList.add('selected');
            }
        };
        list.appendChild(li);
    });

    const doneBtn = document.createElement('button');
    doneBtn.id = 'done-btn';
    doneBtn.textContent = 'Done';
    doneBtn.onclick = () => {
        submitSymptoms();
        optionsContainer.remove();
    };

    optionsContainer.appendChild(list);
    optionsContainer.appendChild(doneBtn);
    chatbox.appendChild(optionsContainer);
    chatbox.scrollTop = chatbox.scrollHeight;
}


function selectSymptom(symptom, btn) {
    if (selectedSymptoms.includes(symptom)) {
        selectedSymptoms.splice(selectedSymptoms.indexOf(symptom), 1);
        btn.classList.remove('selected');
    } else {
        selectedSymptoms.push(symptom);
        btn.classList.add('selected');
    }
}

function showFollowUpOptions() {
    optionsShown = false;
    const optionsContainer = document.createElement('div');
    optionsContainer.className = 'message';
    
    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'options-group';

    const yesBtn = document.createElement('button');
    yesBtn.className = 'option-btn';
    yesBtn.textContent = 'Yes';
    yesBtn.onclick = () => {
        buttonGroup.remove();
        botTypingMessage("How else can I help you?", 1000, showInitialOptions);
    };

    const noBtn = document.createElement('button');
    noBtn.className = 'option-btn';
    noBtn.textContent = 'No';
    noBtn.onclick = () => {
        buttonGroup.remove();
        botTypingMessage("Wishing your pet a safe and good health. Thank you and have a nice day!", 1000);
    };

    buttonGroup.appendChild(yesBtn);
    buttonGroup.appendChild(noBtn);
    optionsContainer.appendChild(buttonGroup);
    chatbox.appendChild(optionsContainer);
    chatbox.scrollTop = chatbox.scrollHeight;
}

async function handleError() {
    optionsShown = false;
    botTypingMessage("Sorry, there was an error. Please try again.", 1000, () => {
        botTypingMessage("How would you like to proceed?", 1000, showInitialOptions);
    });
}

async function submitSymptoms() {
    if (selectedSymptoms.length === 0) {
        alert("Please select at least one symptom.");
        return;
    }

    const userMsg = document.createElement('div');
    userMsg.className = 'message user';
    userMsg.textContent = selectedSymptoms.join(', ');
    chatbox.appendChild(userMsg);

    try {
        const response = await fetch('/api/diagnose', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ symptoms: selectedSymptoms })
        });
        
        if (!response.ok) throw new Error('API error');
        
        const diagnosis = await response.json();
        
        const readableCondition = getDisplayName(diagnosis.condition);
botTypingMessage(`Based on the analysis, your dog might have: ${readableCondition}`, 1500, () => {

            // const linkMsg = document.createElement('div');
            // linkMsg.className = 'message bot';
            // // linkMsg.innerHTML = `Book an appointment <a href="/appointment" target="_blank">here</a>`;
            // chatbox.appendChild(linkMsg);
            
            setTimeout(() => {
                botTypingMessage("Is there anything else I can help you with?", 1000, showFollowUpOptions);
            }, 1500);
        });
    } catch (error) {
        handleError();
    }
}

fileInput.addEventListener('change', async (e) => {
    if (e.target.files.length > 0) {
        const userMsg = document.createElement('div');
        userMsg.className = 'message user';
        userMsg.textContent = "Image uploaded";
        chatbox.appendChild(userMsg);

        try {
            const formData = new FormData();
            formData.append('image', e.target.files[0]);
            
            const response = await fetch('/api/analyze-image', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) throw new Error('API error');
            
            const diagnosis = await response.json();
            botTypingMessage(`Based on the image analysis, your dog is: ${diagnosis.condition}`, 1500, () => {
                // const linkMsg = document.createElement('div');
                // linkMsg.className = 'message bot';
                // // linkMsg.innerHTML = `Book an appointment <a href="/appointment" target="_blank">here</a>.`;
                // chatbox.appendChild(linkMsg);
                
                setTimeout(() => {
                    botTypingMessage("Is there anything else I can help you with?", 1000, showFollowUpOptions);
                }, 1500);
            });
        } catch (error) {
            handleError();
        }
    }
});

// Start the chat
setTimeout(() => botTypingMessage("Hi, how may I assist you today?", 1000, showInitialOptions), 500);
