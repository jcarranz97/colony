import * as Yup from "yup";

export const LoginSchema = Yup.object({
  email: Yup.string().email("Invalid email").required("Email is required"),
  password: Yup.string().required("Password is required"),
});

export const RegisterSchema = Yup.object({
  email: Yup.string().email("Invalid email").required("Email is required"),
  password: Yup.string()
    .min(8, "Password must be at least 8 characters")
    .required("Password is required"),
  first_name: Yup.string().required("First name is required"),
  last_name: Yup.string().required("Last name is required"),
});

export const PaymentMethodSchema = Yup.object({
  name: Yup.string().required("Name is required"),
  method_type: Yup.string()
    .oneOf(["debit", "credit", "cash", "transfer"])
    .required("Type is required"),
  default_currency: Yup.string()
    .oneOf(["USD", "MXN"])
    .required("Currency is required"),
});

const recurrenceConfigShape = Yup.object()
  .when("recurrence_type", {
    is: "weekly",
    then: (s) =>
      s.shape({
        day_of_week: Yup.number()
          .min(0)
          .max(6)
          .required("Day of week is required"),
      }),
  })
  .when("recurrence_type", {
    is: "bi_weekly",
    then: (s) =>
      s.shape({
        interval_days: Yup.number()
          .positive()
          .integer()
          .required("Interval days is required"),
      }),
  })
  .when("recurrence_type", {
    is: "monthly",
    then: (s) =>
      s.shape({
        day_of_month: Yup.number()
          .min(1)
          .max(31)
          .required("Day of month is required"),
        handle_month_end: Yup.boolean().optional(),
      }),
  })
  .when("recurrence_type", {
    is: "custom",
    then: (s) =>
      s.shape({
        interval: Yup.number()
          .positive()
          .integer()
          .required("Interval is required"),
        unit: Yup.mixed()
          .oneOf(["days", "weeks", "months"])
          .required("Unit is required"),
      }),
  });

export const RecurrentExpenseCreateSchema = Yup.object({
  description: Yup.string().required("Name is required"),
  base_amount: Yup.string().required("Amount is required"),
  currency: Yup.string().oneOf(["USD", "MXN"]).required("Currency is required"),
  category: Yup.string()
    .oneOf(["fixed", "variable"])
    .required("Category is required"),
  recurrence_type: Yup.string()
    .oneOf(["weekly", "bi_weekly", "monthly", "custom"])
    .required("Recurrence type is required"),
  recurrence_config: recurrenceConfigShape,
  reference_date: Yup.string().required("Reference date is required"),
  payment_method_id: Yup.string()
    .nullable()
    .required("Payment method is required"),
});

export const RecurrentExpenseSchema = Yup.object({
  description: Yup.string().required("Name is required"),
  base_amount: Yup.string().required("Amount is required"),
  currency: Yup.string().oneOf(["USD", "MXN"]).required("Currency is required"),
  category: Yup.string()
    .oneOf(["fixed", "variable"])
    .required("Category is required"),
  recurrence_type: Yup.string()
    .oneOf(["weekly", "bi_weekly", "monthly", "custom"])
    .required("Recurrence type is required"),
  recurrence_config: recurrenceConfigShape,
  reference_date: Yup.string().optional(),
  payment_method_id: Yup.string().nullable().optional(),
});

export const CycleCreateSchema = Yup.object({
  name: Yup.string().required("Name is required"),
  start_date: Yup.string().required("Start date is required"),
  end_date: Yup.string().required("End date is required"),
  income: Yup.string().optional(),
  generate_from_templates: Yup.boolean().optional(),
});

export const CycleExpenseSchema = Yup.object({
  name: Yup.string().required("Name is required"),
  amount: Yup.string().required("Amount is required"),
  currency: Yup.string().oneOf(["USD", "MXN"]).required("Currency is required"),
  category: Yup.string()
    .oneOf(["fixed", "variable"])
    .required("Category is required"),
  due_date: Yup.string().nullable().optional(),
  payment_method_id: Yup.string().nullable().optional(),
});

export const UpdateProfileSchema = Yup.object({
  first_name: Yup.string().required("First name is required"),
  last_name: Yup.string().required("Last name is required"),
  preferred_currency: Yup.string()
    .oneOf(["USD", "MXN"])
    .required("Preferred currency is required"),
});

export const UpdatePasswordSchema = Yup.object({
  current_password: Yup.string().required("Current password is required"),
  new_password: Yup.string()
    .min(8, "Password must be at least 8 characters")
    .required("New password is required"),
  confirm_password: Yup.string()
    .oneOf([Yup.ref("new_password")], "Passwords must match")
    .required("Confirm password is required"),
});
