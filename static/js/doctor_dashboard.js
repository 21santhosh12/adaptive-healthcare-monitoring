// Global variable to store current appointments
let currentAppointments = [];

// Function to load appointments
function loadAppointments(type = 'upcoming') {
    fetch(`/appointments/doctor/${doctorId}?type=${type}`)
        .then(response => response.json())
        .then(appointments => {
            const appointmentsList = document.getElementById('appointmentsList');
            appointmentsList.innerHTML = '';
            
            if (!appointments || appointments.length === 0) {
                appointmentsList.innerHTML = `<p class="text-muted">No ${type} appointments found.</p>`;
                return;
            }
            
            appointments.forEach(apt => {
                const card = document.createElement('div');
                card.className = `card mb-3 appointment-card ${getPriorityClass(apt.priority_level)}`;
                
                const priorityBadge = `<span class="badge bg-${getPriorityBadgeClass(apt.priority_level)}">
                    ${getPriorityLabel(apt.priority_level)}
                </span>`;
                
                card.innerHTML = `
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="mb-0">${apt.patient_name}</h6>
                            <div>
                                ${priorityBadge}
                                <span class="badge bg-primary">${apt.time}</span>
                            </div>
                        </div>
                        <p class="text-muted small mb-2">${apt.symptoms}</p>
                        ${type === 'upcoming' ? `
                            <div class="text-end">
                                <button class="btn btn-primary btn-sm" onclick="showUpdateModal('${apt.id}')">
                                    Update
                                </button>
                            </div>
                        ` : ''}
                    </div>
                `;
                
                appointmentsList.appendChild(card);
            });
        })
        .catch(error => {
            console.error('Error loading appointments:', error);
            document.getElementById('appointmentsList').innerHTML = 
                '<p class="text-danger">Error loading appointments. Please try again.</p>';
        });
}

// Function to update appointment
function updateAppointment(appointmentId) {
    const status = document.getElementById('appointmentStatus').value;
    const diagnosis = document.getElementById('diagnosis').value;
    const prescription = document.getElementById('prescription').value;
    const notes = document.getElementById('doctorNotes').value;
    const nextVisitNeeded = document.getElementById('nextVisitNeeded').checked;
    const nextVisitRecommendation = document.getElementById('nextVisitRecommendation').value;

    // Validate required fields
    if (!diagnosis.trim() || !prescription.trim()) {
        alert('Please fill in both diagnosis and prescription fields');
        return;
    }

    // Show loading state
    const updateBtn = document.getElementById('updateAppointmentBtn');
    const originalText = updateBtn.textContent;
    updateBtn.textContent = 'Updating...';
    updateBtn.disabled = true;

    fetch(`/appointments/${appointmentId}/update`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            status: status,
            diagnosis: diagnosis,
            prescription: prescription,
            notes: notes,
            next_visit_needed: nextVisitNeeded,
            next_visit_recommendation: nextVisitRecommendation
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('updateAppointmentModal'));
        modal.hide();
        
        // Show success message
        alert('Appointment updated successfully');
        
        // Refresh the appointments list
        loadAppointments('upcoming');
    })
    .catch(error => {
        alert('Failed to update appointment: ' + error.message);
        console.error('Error:', error);
    })
    .finally(() => {
        // Reset button state
        updateBtn.textContent = originalText;
        updateBtn.disabled = false;
    });
}

// Function to format time to 24-hour format
function formatTime(time) {
    // Convert 24-hour time to display format (you can customize this based on preference)
    const [hours, minutes] = time.split(':');
    return `${hours}:${minutes}`;
}

// Function to load time slots
function loadTimeSlots() {
    const timeSelect = document.getElementById('appointmentTime');
    if (!timeSelect) {
        console.error('Time select element not found');
        return;
    }
    
    const currentDate = new Date().toISOString().split('T')[0];
    
    timeSelect.innerHTML = '<option value="">Loading time slots...</option>';
    timeSelect.disabled = true;
    
    fetch(`/doctor/availability/${doctorId}?date=${currentDate}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch time slots');
            }
            return response.json();
        })
        .then(data => {
            if (!data || !Array.isArray(data.available_slots)) {
                throw new Error('Invalid time slots data received');
            }
            
            timeSelect.innerHTML = '<option value="">Select Time</option>';
            
            if (!data.is_available) {
                timeSelect.innerHTML = '<option value="">Doctor not available today</option>';
                timeSelect.disabled = true;
                return;
            }
            
            const availableSlots = data.available_slots || [];
            if (availableSlots.length === 0) {
                timeSelect.innerHTML = '<option value="">No available slots for today</option>';
                timeSelect.disabled = true;
                return;
            }
            
            // Filter out past time slots
            const currentTime = new Date();
            const availableFutureSlots = availableSlots.filter(slot => {
                const [time, period] = slot.split(' ');
                const [hours, minutes] = time.split(':');
                const slotTime = new Date(currentDate);
                slotTime.setHours(
                    period === 'PM' && hours !== '12' ? parseInt(hours) + 12 : 
                    period === 'AM' && hours === '12' ? 0 : parseInt(hours)
                );
                slotTime.setMinutes(parseInt(minutes));
                return slotTime > currentTime;
            });
            
            if (availableFutureSlots.length === 0) {
                timeSelect.innerHTML = '<option value="">No available slots remaining today</option>';
                timeSelect.disabled = true;
                return;
            }
            
            // Add available time slots
            availableFutureSlots.forEach(slot => {
                const option = document.createElement('option');
                option.value = slot;
                option.textContent = slot;
                timeSelect.appendChild(option);
            });
            
            timeSelect.disabled = false;
        })
        .catch(error => {
            console.error('Error loading time slots:', error);
            timeSelect.innerHTML = '<option value="">Error loading time slots</option>';
            timeSelect.disabled = true;
        });
}

// Helper function to format time for display
function formatTimeForDisplay(time) {
    const [hours, minutes] = time.split(':').map(Number);
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
}

// Function to show update modal
function showUpdateModal(appointmentId) {
    const appointment = currentAppointments.find(apt => apt.id === appointmentId);
    if (!appointment) {
        alert('Appointment not found');
        return;
    }
    
    // Populate modal fields
    document.getElementById('appointmentId').value = appointmentId;
    document.getElementById('patientName').value = appointment.patient_name;
    document.getElementById('symptoms').value = appointment.symptoms || '';
    document.getElementById('diagnosis').value = appointment.diagnosis || '';
    document.getElementById('prescription').value = appointment.prescription || '';
    document.getElementById('doctorNotes').value = appointment.notes || '';
    document.getElementById('appointmentStatus').value = 'completed';
    
    // Reset next visit fields
    document.getElementById('nextVisitNeeded').checked = false;
    document.getElementById('nextVisitRecommendation').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('updateAppointmentModal'));
    modal.show();
}

// Helper functions
function getPriorityClass(priority) {
    switch(priority) {
        case 1: return 'border-danger';
        case 2: return 'border-warning';
        default: return 'border-primary';
    }
}

function getPriorityLabel(priority) {
    switch(priority) {
        case 1: return 'Emergency';
        case 2: return 'Urgent';
        default: return 'Routine';
    }
}

function getStatusBadge(status) {
    const badges = {
        'scheduled': 'bg-primary',
        'completed': 'bg-success',
        'cancelled': 'bg-danger',
        'no-show': 'bg-warning'
    };
    return `<span class="badge ${badges[status] || 'bg-secondary'}">${status}</span>`;
}

// Function to show response modal with proper error handling and UI feedback
function showResponseModal(appointmentId, appointmentData) {
    try {
        // Parse appointment data if it's a string
        const appointment = typeof appointmentData === 'string' ? JSON.parse(appointmentData) : appointmentData;
        
        // Set modal values
        document.getElementById('pendingAppointmentId').value = appointmentId;
        document.getElementById('pendingPatientName').value = appointment.patient_name || '';
        document.getElementById('pendingSymptoms').value = appointment.symptoms || '';
        document.getElementById('pendingPriority').value = getPriorityLabel(appointment.priority_level || 3);
        
        // Reset form fields
        document.getElementById('appointmentTime').value = '';
        document.getElementById('rejectionReason').value = '';
        
        // Show acceptance fields, hide rejection fields
        document.getElementById('acceptanceFields').style.display = 'block';
        document.getElementById('rejectionFields').style.display = 'none';
        
        // Load available time slots
        loadTimeSlots();
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('respondAppointmentModal'));
        modal.show();
    } catch (error) {
        console.error('Error showing response modal:', error);
        alert('Error loading appointment details. Please try again.');
    }
}

// Function to handle appointment rejection
function rejectAppointment() {
    const appointmentId = document.getElementById('pendingAppointmentId').value;
    const reasonField = document.getElementById('rejectionReason');
    
    if (!appointmentId) {
        alert('Invalid appointment ID');
        return;
    }
    
    // Show rejection fields
    document.getElementById('acceptanceFields').style.display = 'none';
    document.getElementById('rejectionFields').style.display = 'block';
    
    // If rejection reason is already filled, proceed with rejection
    if (reasonField.value.trim()) {
        submitRejection(appointmentId, reasonField.value.trim());
    }
}

// Function to submit rejection
function submitRejection(appointmentId, reason) {
    if (!reason) {
        alert('Please provide a reason for rejection');
        return;
    }
    
    const rejectButton = document.querySelector('button[onclick="rejectAppointment()"]');
    rejectButton.disabled = true;
    rejectButton.textContent = 'Rejecting...';
    
    fetch(`/appointments/${appointmentId}/respond`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            action: 'reject',
            reason: reason
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to reject appointment');
        }
        return response.json();
    })
    .then(result => {
        if (result.error) {
            throw new Error(result.error);
        }
        
        // Close modal and refresh appointments
        const modal = bootstrap.Modal.getInstance(document.getElementById('respondAppointmentModal'));
        modal.hide();
        
        // Refresh pending appointments
        loadPendingAppointments();
        
        alert('Appointment request rejected successfully');
    })
    .catch(error => {
        console.error('Error rejecting appointment:', error);
        alert('Failed to reject appointment: ' + error.message);
    })
    .finally(() => {
        rejectButton.disabled = false;
        rejectButton.textContent = 'Reject';
    });
}

// Add event listener for appointment response form
document.getElementById('appointmentResponseForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const appointmentId = document.getElementById('pendingAppointmentId').value;
    const time = document.getElementById('appointmentTime').value;
    
    if (!time) {
        alert('Please select an appointment time');
        return;
    }
    
    const submitButton = this.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    submitButton.textContent = 'Scheduling...';
    
    fetch(`/appointments/${appointmentId}/respond`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            action: 'accept',
            appointment_time: time
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to schedule appointment');
        return response.json();
    })
    .then(result => {
        if (result.error) throw new Error(result.error);
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('respondAppointmentModal'));
        modal.hide();
        
        // Refresh both sections
        loadPendingAppointments();
        loadAppointments('upcoming');
        
        alert('Appointment scheduled successfully');
    })
    .catch(error => {
        console.error('Error scheduling appointment:', error);
        alert('Failed to schedule appointment: ' + error.message);
    })
    .finally(() => {
        submitButton.disabled = false;
        submitButton.textContent = 'Accept & Schedule';
    });
});

// Event listener for appointment update form
document.getElementById('appointmentUpdateForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const appointmentId = document.getElementById('appointmentId').value;
    updateAppointment(appointmentId);
});

// Add this function to check and set default availability
function checkAndSetDefaultAvailability() {
    const currentDate = new Date().toISOString().split('T')[0];
    
    fetch(`/doctor/availability/${doctorId}`)
        .then(response => response.json())
        .then(data => {
            if (!data.is_available) {
                // Set default availability for today
                fetch('/doctor/availability', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        doctor_id: doctorId,
                        date: currentDate,
                        is_available: true,
                        available_slots: [
                            '9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM',
                            '11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM',
                            '2:00 PM', '2:30 PM', '3:00 PM', '3:30 PM',
                            '4:00 PM', '4:30 PM', '5:00 PM', '5:30 PM',
                            '6:00 PM', '6:30 PM', '7:00 PM', '7:30 PM',
                            '8:00 PM', '8:30 PM', '9:00 PM', '9:30 PM',
                            '10:00 PM', '10:30 PM', '11:00 PM'
                        ]
                    })
                })
                .then(response => response.json())
                .then(result => {
                    if (result.error) {
                        console.error('Error setting default availability:', result.error);
                    }
                })
                .catch(error => {
                    console.error('Error setting default availability:', error);
                });
            }
        })
        .catch(error => {
            console.error('Error checking availability:', error);
        });
}

// Update the initialization
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Check and set default availability
        checkAndSetDefaultAvailability();
        
        // Initialize all modals
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modalEl => {
            new bootstrap.Modal(modalEl);
        });
        
        // Load appointments
        loadAppointments('upcoming');
        
        // Set up auto-refresh
        setInterval(() => {
            loadAppointments('upcoming');
        }, 30000);
        
    } catch (error) {
        console.error('Error initializing dashboard:', error);
    }
});

// Add getPriorityBadgeClass function
function getPriorityBadgeClass(priority) {
    switch(priority) {
        case 1: return 'danger';
        case 2: return 'warning';
        default: return 'primary';
    }
} 