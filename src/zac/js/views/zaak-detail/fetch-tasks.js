import { apiCall } from '../../utils/fetch';


const fetchTasks = (node) => {
    const { url, forZaak } = node.dataset;

    const fullUrl = `${url}?zaak=${forZaak}`;
    apiCall(fullUrl)
        .then(response => response.text())
        .then(content => {node.innerHTML = content;})
        .catch(console.error);
};

const nodes = document.querySelectorAll('.fetch-tasks');
Array.from(nodes).forEach(fetchTasks);
