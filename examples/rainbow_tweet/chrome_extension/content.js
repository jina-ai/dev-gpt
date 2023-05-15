console.log('Twitter Rewrite: Content script loaded');
let openai_api_key = '';

// Get OPENAI_API_KEY from chrome storage
chrome.storage.sync.get({
  openai_api_key: ''
}, function(items) {
  openai_api_key = items.openai_api_key;
});

let observer = new MutationObserver((mutations) => {
    console.log('Twitter Rewrite: DOM mutation detected');
    // For each mutation
    mutations.forEach((mutation) => {
        // If nodes were added
        if (mutation.addedNodes) {
            mutation.addedNodes.forEach((node) => {
                // If the added node (or its descendants) contains a tweet
                let tweets = node.querySelectorAll('[data-testid="tweet"]');
                tweets.forEach((tweet) => {
                    // If the tweet doesn't already have a modify button
                    if (!tweet.querySelector('.modify-button')) {
                        // Create new button
                        let button = document.createElement('button');
                        if (openai_api_key === '') {
                            button.innerText = 'Set OPENAI_API_KEY by clicking the extension icon';
                            button.disabled = true;
                        } else {
                            button.innerText = '🦄';
                            button.disabled = false;
                        }
                        button.className = 'modify-button';

                        // Add event listener for button click
                        button.addEventListener('click', function() {
                            let thisButton = this;
                            // Send tweet to API
                            let originalTweet = tweet.querySelector('[data-testid="tweetText"]').innerText;
                            this.disabled = true;
                            this.innerText = 'Loading...';
                            fetch('https://gptdeploy-61694dd6a3.wolf.jina.ai/post', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'accept': 'application/json'
                                },
                                body: JSON.stringify({
                                    "data": [{"text": JSON.stringify({
                                            "tweet": originalTweet,
                                            "OPENAI_API_KEY": openai_api_key
                                    }) }]
                                })
                            })
                            .then(response => response.json())
                            .then(data => {
                                let modifiedTweet = JSON.parse(data.data[0].text).positive_tweet;
                                let rainbowTweet = Array.from(modifiedTweet).map((char, i) =>
                                    `<span class="rainbow-text" style="--i: ${i};">${char}</span>`
                                ).join('');

                                // Create a new element node to contain the HTML
                                let newTweet = document.createElement('span');
                                newTweet.innerHTML = rainbowTweet;
                                // Replace the old text node with the new element node
                                tweet.querySelector('[data-testid="tweetText"]').replaceWith(newTweet);
                                // Remove the button
                                thisButton.remove();
                            });
                        });

                        // Find the actions container and inject the button into it
                        let actionGroups = tweet.querySelectorAll('div[role="group"]');
                        let actionsContainer = actionGroups[actionGroups.length - 1];
                        actionsContainer.appendChild(button);
                    }
                });
            });
        }
    });
});

// Start observing the document with the configured parameters
observer.observe(document.body, { childList: true, subtree: true });
