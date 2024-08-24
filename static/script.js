document.addEventListener('DOMContentLoaded', function() {
    const exercises = document.querySelectorAll('.exercise');
    const modal = document.getElementById('exercise-log-modal');
    const modalExerciseName = document.getElementById('modal-exercise-name');
    const modalSets = document.getElementById('modal-sets');
    const modalReps = document.getElementById('modal-reps');
    const modalWeight = document.getElementById('modal-weight');
    const modalFeedback = document.getElementById('modal-feedback');
    const logExerciseBtn = document.getElementById('log-exercise');
    const closeModalBtn = document.getElementById('close-modal');

    let currentExerciseIndex = 0;

    function showExercise(index) {
        exercises.forEach((exercise, i) => {
            if (i === index) {
                exercise.style.display = 'block';
            } else {
                exercise.style.display = 'none';
            }
        });
    }

    document.getElementById('prev-exercise')?.addEventListener('click', function() {
        currentExerciseIndex = Math.max(0, currentExerciseIndex - 1);
        showExercise(currentExerciseIndex);
    });

    document.getElementById('next-exercise')?.addEventListener('click', function() {
        currentExerciseIndex = Math.min(exercises.length - 1, currentExerciseIndex + 1);
        showExercise(currentExerciseIndex);
    });

    document.getElementById('skip-exercise')?.addEventListener('click', function() {
        currentExerciseIndex = Math.min(exercises.length - 1, currentExerciseIndex + 1);
        showExercise(currentExerciseIndex);
    });

    exercises.forEach(exercise => {
        exercise.addEventListener('click', function() {
            const exerciseName = this.dataset.exercise;
            modalExerciseName.textContent = exerciseName;
            // You may want to pre-fill the modal inputs with existing data if available
            modal.style.display = 'block';
        });
    });

    closeModalBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    logExerciseBtn.addEventListener('click', function() {
        const exerciseData = {
            exercise_name: modalExerciseName.textContent,
            sets: modalSets.value,
            reps: modalReps.value,
            weight: modalWeight.value,
            feedback: modalFeedback.value,
            workout_id: workoutId // You need to pass this value from your template
        };

        fetch('/log_exercise', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(exerciseData),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Exercise logged successfully!');
                modal.style.display = 'none';
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    });

    // Increase/decrease buttons functionality
    const increaseDecreaseButtons = document.querySelectorAll('.increase-sets, .decrease-sets, .increase-reps, .decrease-reps, .increase-weight, .decrease-weight');
    increaseDecreaseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
            const value = parseFloat(input.value);
            const step = input.step ? parseFloat(input.step) : 1;
            if (this.classList.contains('increase-sets') || this.classList.contains('increase-reps') || this.classList.contains('increase-weight')) {
                input.value = (value + step).toFixed(2);
            } else {
                input.value = Math.max(0, (value - step)).toFixed(2);
            }
        });
    });

    // Initialize the first exercise
    showExercise(currentExerciseIndex);
});