
export const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
        alert('Copied to clipboard');
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
};

export const weekdaysOptions = [
    { value: 1, labelKey: 'mon' },
    { value: 2, labelKey: 'tue' },
    { value: 3, labelKey: 'wed' },
    { value: 4, labelKey: 'thu' },
    { value: 5, labelKey: 'fri' },
    { value: 6, labelKey: 'sat' },
    { value: 0, labelKey: 'sun' }
];

export const buildCronString = (form) => {
    const { type, interval, time, weekdays, monthDay } = form;
    // Parse time HH:MM
    let [hour, minute] = time.split(':').map(Number);
    if (isNaN(hour)) hour = 10;
    if (isNaN(minute)) minute = 0;

    switch (type) {
        case 'interval':
            if (interval.unit === 'minutes') {
                // Every N minutes
                return `*/${interval.value} * * * *`;
            } else {
                // Every N hours at minute 0
                return `0 */${interval.value} * * *`;
            }
        case 'daily':
            // At HH:MM every day
            return `${minute} ${hour} * * *`;
        case 'weekly':
            // At HH:MM on specific days
            const days = weekdays.length > 0 ? weekdays.sort().join(',') : '*';
            return `${minute} ${hour} * * ${days}`;
        case 'monthly':
            // At HH:MM on specific day of month
            return `${minute} ${hour} ${monthDay} * *`;
        default:
            return '*/30 * * * *';
    }
};

export const formatCron = (input, t) => {
    if (!input) return '-';
    
    // Handle structured schedule object from DB
    if (typeof input === 'object') {
        const { schedule_type, interval_value, interval_unit, run_time, weekdays, month_day } = input;
        
        if (schedule_type === 'interval') {
             return t('cron_builder.every') + ' ' + interval_value + ' ' + t('cron_builder.units.' + interval_unit);
        }
        if (schedule_type === 'daily') {
             return t('cron_builder.types.daily') + ' ' + run_time;
        }
        if (schedule_type === 'weekly') {
             let daysText = weekdays;
             if (weekdays) {
                const dayNums = weekdays.split(',').map(Number);
                const dayNames = dayNums.map(num => {
                    const opt = weekdaysOptions.find(o => o.value === num);
                    return opt ? t('cron_builder.weekdays_items.' + opt.labelKey) : num;
                });
                daysText = dayNames.join(', ');
             }
             return t('cron_builder.types.weekly') + ' ' + daysText + ' ' + run_time;
        }
        if (schedule_type === 'monthly') {
             return t('cron_builder.types.monthly') + ' ' + month_day + ' ' + run_time;
        }
        return schedule_type;
    }

    // Handle Cron String (Preview)
    const cron = input;
    if (cron.startsWith('*/')) {
        const parts = cron.split(' ');
        const minPart = parts[0];
        const val = minPart.replace('*/', '');
        return t('cron_builder.every') + ' ' + val + ' ' + t('cron_builder.units.minutes');
    }
    if (cron.startsWith('0 */')) {
        const parts = cron.split(' ');
        const hourPart = parts[1];
        const val = hourPart.replace('*/', '');
        return t('cron_builder.every') + ' ' + val + ' ' + t('cron_builder.units.hours');
    }
    const parts = cron.split(' ');
    if (parts.length === 5) {
        const [m, h, d, mo, w] = parts;
        const time = `${h.padStart(2, '0')}:${m.padStart(2, '0')}`;
        
        if (d === '*' && mo === '*' && w === '*') {
             return t('cron_builder.types.daily') + ' ' + time;
        }
        if (d === '*' && mo === '*' && w !== '*') {
             let daysText = w;
             if (w !== '*') {
                const dayNums = w.split(',').map(Number);
                const dayNames = dayNums.map(num => {
                    const opt = weekdaysOptions.find(o => o.value === num);
                    return opt ? t('cron_builder.weekdays_items.' + opt.labelKey) : num;
                });
                daysText = dayNames.join(', ');
             }
             return t('cron_builder.types.weekly') + ' ' + daysText + ' ' + time;
        }
        if (d !== '*' && mo === '*' && w === '*') {
             return t('cron_builder.types.monthly') + ' ' + d + ' ' + time;
        }
    }
    return cron;
};
