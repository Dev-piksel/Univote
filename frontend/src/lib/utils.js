/**
 * Consistently formats a student's full name from its components.
 * Handles missing middle initials gracefully.
 * 
 * @param {Object} student - Object containing first_name, last_name, and optional middle_initial
 * @returns {string} The formatted full name
 */
export function formatFullName(student) {
    if (!student) return 'Unknown Node';
    
    const fn = student.first_name || '';
    const ln = student.last_name || '';
    const mi = student.middle_initial || '';
    
    if (!fn && !ln) return 'Anonymous Node';
    
    const formattedMI = mi ? `${mi[0].toUpperCase()}. ` : '';
    return `${fn} ${formattedMI}${ln}`.trim();
}

/**
 * Standardizes the department/program display format.
 * Ensures the 'CCS-' prefix is consistently applied.
 * 
 * @param {string} program - The program/course name (e.g., 'BSIT')
 * @returns {string} The standardized department-program string
 */
export function formatDepartment(program) {
    if (!program) return 'CCS-UNDEFINED';
    if (program.startsWith('CCS-')) return program;
    return `CCS-${program}`;
}
