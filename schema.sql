-- Ethara Seat Allocation & Project Mapping System
-- Database schema (SQLite / PostgreSQL compatible DDL)

CREATE TABLE projects (
	id INTEGER NOT NULL, 
	name VARCHAR NOT NULL, 
	description VARCHAR, 
	manager_name VARCHAR, 
	status VARCHAR, 
	created_at DATETIME, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_projects_id ON projects (id);
CREATE UNIQUE INDEX ix_projects_name ON projects (name);

CREATE TABLE seats (
	id INTEGER NOT NULL, 
	floor INTEGER NOT NULL, 
	zone VARCHAR NOT NULL, 
	bay INTEGER NOT NULL, 
	seat_number VARCHAR NOT NULL, 
	status VARCHAR, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_seat_location UNIQUE (floor, zone, seat_number)
);
CREATE INDEX ix_seat_floor_zone ON seats (floor, zone);
CREATE INDEX ix_seats_zone ON seats (zone);
CREATE INDEX ix_seats_seat_number ON seats (seat_number);
CREATE INDEX ix_seats_id ON seats (id);
CREATE INDEX ix_seats_status ON seats (status);
CREATE INDEX ix_seats_floor ON seats (floor);

CREATE TABLE employees (
	id INTEGER NOT NULL, 
	employee_code VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	email VARCHAR NOT NULL, 
	department VARCHAR, 
	role VARCHAR, 
	joining_date DATE, 
	status VARCHAR, 
	project_id INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
CREATE UNIQUE INDEX ix_employees_employee_code ON employees (employee_code);
CREATE INDEX ix_employees_name ON employees (name);
CREATE INDEX ix_employees_project_id ON employees (project_id);
CREATE UNIQUE INDEX ix_employees_email ON employees (email);
CREATE INDEX ix_employees_id ON employees (id);

CREATE TABLE seat_allocations (
	id INTEGER NOT NULL, 
	employee_id INTEGER NOT NULL, 
	seat_id INTEGER NOT NULL, 
	project_id INTEGER, 
	allocation_status VARCHAR, 
	allocation_date DATETIME, 
	released_date DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id), 
	FOREIGN KEY(seat_id) REFERENCES seats (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
CREATE INDEX ix_seat_allocations_id ON seat_allocations (id);
CREATE INDEX ix_seat_allocations_seat_id ON seat_allocations (seat_id);
CREATE INDEX ix_seat_allocations_allocation_status ON seat_allocations (allocation_status);
CREATE INDEX ix_seat_allocations_employee_id ON seat_allocations (employee_id);
