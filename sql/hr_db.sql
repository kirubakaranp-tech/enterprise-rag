DROP TABLE IF EXISTS payslips;
DROP TABLE IF EXISTS leaves;
DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    emp_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    joining_date DATE
);

CREATE TABLE leaves (
    emp_id TEXT NOT NULL REFERENCES employees(emp_id),
    leave_type TEXT NOT NULL,
    total_days INTEGER NOT NULL,
    used_days INTEGER NOT NULL,
    PRIMARY KEY (emp_id, leave_type)
);

CREATE TABLE payslips (
    emp_id TEXT NOT NULL REFERENCES employees(emp_id),
    month TEXT NOT NULL,
    gross_pay INTEGER NOT NULL,
    deductions INTEGER NOT NULL,
    net_pay INTEGER NOT NULL,
    PRIMARY KEY (emp_id, month)
);
