const API_URL = "http://localhost:8000";

export const API = {
  auth: {
    register: (data) => fetch(`${API_URL}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }).then(r => r.json()),
    
    login: (data) => fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }).then(r => r.json()),
    
    logout: (token) => fetch(`${API_URL}/api/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    }).then(r => r.json()),
  },
  
  books: {
    list: (limit = 50, offset = 0) => 
      fetch(`${API_URL}/api/books?limit=${limit}&offset=${offset}`).then(r => r.json()),
    
    get: (id) => fetch(`${API_URL}/api/books/${id}`).then(r => r.json()),
    
    search: (query = "programming", limit = 20) =>
      fetch(`${API_URL}/api/books/search?query=${query}&limit=${limit}`).then(r => r.json()),
    
    import: (query = "programming", limit = 50) =>
      fetch(`${API_URL}/api/books/import?query=${query}&limit=${limit}`, { method: "POST" }).then(r => r.json()),
  },
  
  cart: {
    add: (bookId, userId) => 
      fetch(`${API_URL}/api/cart/add/${bookId}?user_id=${userId}`, { method: "POST" }).then(r => r.json()),
    
    remove: (bookId, userId) =>
      fetch(`${API_URL}/api/cart/remove/${bookId}?user_id=${userId}`, { method: "DELETE" }).then(r => r.json()),
    
    get: (userId) => fetch(`${API_URL}/api/cart?user_id=${userId}`).then(r => r.json()),
    
    checkout: (userId) => fetch(`${API_URL}/api/cart/checkout?user_id=${userId}`, { method: "POST" }).then(r => r.json()),
  },
  
  loans: {
    user: (userId, status) => {
      const url = status 
        ? `${API_URL}/api/loans/user/${userId}?status=${status}`
        : `${API_URL}/api/loans/user/${userId}`;
      return fetch(url).then(r => r.json());
    },
    
    list: (status) => 
      fetch(`${API_URL}/api/loans${status ? `?status=${status}` : ''}`).then(r => r.json()),
    
    approve: (loanId, adminId) => fetch(`${API_URL}/api/loans/${loanId}/approve?admin_id=${adminId}`, { method: "POST" }).then(r => r.json()),
    
    return: (loanId) => fetch(`${API_URL}/api/loans/${loanId}/return`, { method: "POST" }).then(r => r.json()),
    
    cancel: (loanId) => fetch(`${API_URL}/api/loans/${loanId}/cancel`, { method: "POST" }).then(r => r.json()),
    
    transfer: (loanId, userId) => fetch(`${API_URL}/api/loans/transfer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ loan_id: loanId, user_id: userId }),
    }).then(r => r.json()),
  },
  
  audit: (limit = 50) => fetch(`${API_URL}/api/audit?limit=${limit}`).then(r => r.json()),
};

export default API;