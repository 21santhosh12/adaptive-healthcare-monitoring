// Store email for OTP verification
let pendingVerificationEmail = '';

// Signup function
document.getElementById('signupForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const role = document.getElementById('signupRole').value;
    
    const data = {
        name: name,
        email: email,
        password: password,
        role: role
    };
    
    // Add doctor-specific fields if role is doctor
    if (role === 'doctor') {
        data.qualification = document.getElementById('doctorQualification').value;
        data.specialization = document.getElementById('doctorSpecialization').value;
        data.experience = parseInt(document.getElementById('doctorExperience').value) || 0;
    }
    
    fetch('/signup/initiate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // Store email for OTP verification
        pendingVerificationEmail = data.email;
        
        // Show success message
        alert('Registration initiated! Please contact the admin for OTP verification.\nAdmin Email: santhosh6382572352@gmail.com');
        
        // Close signup modal
        const signupModal = bootstrap.Modal.getInstance(document.getElementById('signupModal'));
        signupModal.hide();
        
        // Open OTP modal
        const otpModal = new bootstrap.Modal(document.getElementById('otpModal'));
        otpModal.show();
    })
    .catch(error => {
        console.error('Signup error:', error);
        alert('Signup failed. Please try again.');
    });
});

// OTP verification
document.getElementById('otpForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const otp = document.getElementById('otpInput').value;
    
    fetch('/signup/verify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: pendingVerificationEmail,
            otp: otp
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        alert('Account verified successfully! Please login.');
        
        // Close OTP modal
        const otpModal = bootstrap.Modal.getInstance(document.getElementById('otpModal'));
        otpModal.hide();
        
        // Open login modal
        const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
        loginModal.show();
        
        // Clear stored email
        pendingVerificationEmail = '';
    })
    .catch(error => {
        console.error('OTP verification error:', error);
        alert('Verification failed. Please try again.');
    });
});

// Authentication functions
document.getElementById('loginForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email: email,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // Store user data
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Update UI
        updateAuthUI(true);
        
        // Close login modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
        modal.hide();
        
        // Check if doctor needs to set availability
        if (data.user.role === 'doctor' && data.user.needs_availability_check) {
            checkDoctorAvailability();
        } else {
            // Redirect to dashboard if not already there
            if (window.location.pathname !== '/dashboard') {
                window.location.href = '/dashboard';
            }
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        alert('Login failed. Please try again.');
    });
});

function logout() {
    fetch('/logout')
        .then(response => response.json())
        .then(data => {
            localStorage.removeItem('user');
            updateAuthUI(false);
            window.location.href = '/';
        })
        .catch(error => console.error('Logout error:', error));
}

function updateAuthUI(isLoggedIn) {
    const loginNav = document.getElementById('loginNav');
    const logoutNav = document.getElementById('logoutNav');
    const signupNav = document.getElementById('signupNav');
    
    if (isLoggedIn) {
        loginNav.style.display = 'none';
        signupNav.style.display = 'none';
        logoutNav.style.display = 'block';
    } else {
        loginNav.style.display = 'block';
        signupNav.style.display = 'block';
        logoutNav.style.display = 'none';
    }
}

// Check authentication status on page load
document.addEventListener('DOMContentLoaded', function() {
    const user = localStorage.getItem('user');
    updateAuthUI(!!user);
});

// Utility functions
function formatDate(date) {
    return new Date(date).toLocaleString();
}

function formatVitalSign(value, unit) {
    return `${value} ${unit}`;
}

// Error handling
function handleApiError(error, message = 'An error occurred') {
    console.error(error);
    alert(message);
}

function checkDoctorAvailability() {
    if (confirm('Are you available for appointments today?')) {
        setDoctorAvailability(true);
    } else {
        setDoctorAvailability(false);
    }
}

function setDoctorAvailability(isAvailable) {
    fetch('/doctor/availability/status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            is_available: isAvailable
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // Redirect to dashboard
        window.location.href = '/dashboard';
    })
    .catch(error => {
        console.error('Error setting availability:', error);
        alert('Failed to set availability. Please try again.');
    });
} 