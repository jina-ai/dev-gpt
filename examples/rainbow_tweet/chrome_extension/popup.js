// Saving options to chrome.storage
function save_options() {
  let openai_api_key = document.getElementById('openai_api_key').value;
  chrome.storage.sync.set({
    openai_api_key: openai_api_key
  }, function() {
    // Update status to let user know options were saved.
    let status = document.getElementById('status');
    status.textContent = 'Options saved.';
    setTimeout(function() {
      status.textContent = '';
    }, 750);
  });
}

// Restores options from chrome.storage
function restore_options() {
  chrome.storage.sync.get({
    openai_api_key: ''
  }, function(items) {
    document.getElementById('openai_api_key').value = items.openai_api_key;
  });
}

document.addEventListener('DOMContentLoaded', restore_options);
document.getElementById('optionForm').addEventListener('submit', function(event) {
  event.preventDefault();
  save_options();
});






