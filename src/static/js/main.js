function redirect_if_needed(data) {
    if (data.redirect) {
        window.location.href = data.redirect;
        return true
    }

    return false
}


document.querySelector('form').addEventListener('submit', (event) => {
  event.preventDefault(); // stop the default form submission
  const form = event.target;
  const url = form.action;
  const formData = new FormData(form);

  fetch(url, {
    method: 'POST',
    body: formData
  })
  .then(response => {
    console.log(response);
  })
  .catch(error => {
    console.error(error);
  });
});


$(document).ready(function (event) {
    $("#ask-new-btn").click(() => {
        get_daily_paper(true)
    })
})
