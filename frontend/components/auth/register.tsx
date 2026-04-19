"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Formik } from "formik";
import {
  Button,
  Card,
  Input,
  Label,
  TextField,
  FieldError,
  Spinner,
} from "@heroui/react";
import { RegisterSchema } from "@/helpers/schemas";
import { register, loginWithForm } from "@/lib/auth.api";
import { createAuthCookie } from "@/actions/auth.action";

export function Register() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  return (
    <Card className="w-full max-w-md p-6">
      <Card.Header className="pb-2">
        <Card.Title className="text-2xl">Create your account</Card.Title>
        <Card.Description>Start managing your expenses</Card.Description>
      </Card.Header>
      <Card.Content>
        <Formik
          initialValues={{
            email: "",
            password: "",
            first_name: "",
            last_name: "",
          }}
          validationSchema={RegisterSchema}
          onSubmit={async (values, { setSubmitting }) => {
            setError(null);
            const result = await register(values);
            if (!result.success) {
              setError(result.error.message);
              setSubmitting(false);
              return;
            }
            const loginResult = await loginWithForm(
              values.email,
              values.password,
            );
            if (loginResult.success) {
              await createAuthCookie(loginResult.data.access_token);
              router.replace("/cycles");
            } else {
              router.replace("/login");
            }
            setSubmitting(false);
          }}
        >
          {({
            values,
            errors,
            touched,
            setFieldValue,
            handleSubmit,
            isSubmitting,
          }) => (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="grid grid-cols-2 gap-4">
                <TextField
                  isInvalid={!!errors.first_name && !!touched.first_name}
                  value={values.first_name}
                  onChange={(v) => setFieldValue("first_name", v)}
                >
                  <Label>First Name</Label>
                  <Input />
                  {touched.first_name && errors.first_name && (
                    <FieldError>{errors.first_name}</FieldError>
                  )}
                </TextField>
                <TextField
                  isInvalid={!!errors.last_name && !!touched.last_name}
                  value={values.last_name}
                  onChange={(v) => setFieldValue("last_name", v)}
                >
                  <Label>Last Name</Label>
                  <Input />
                  {touched.last_name && errors.last_name && (
                    <FieldError>{errors.last_name}</FieldError>
                  )}
                </TextField>
              </div>
              <TextField
                isInvalid={!!errors.email && !!touched.email}
                value={values.email}
                onChange={(v) => setFieldValue("email", v)}
              >
                <Label>Email</Label>
                <Input type="email" autoComplete="email" />
                {touched.email && errors.email && (
                  <FieldError>{errors.email}</FieldError>
                )}
              </TextField>
              <TextField
                isInvalid={!!errors.password && !!touched.password}
                value={values.password}
                onChange={(v) => setFieldValue("password", v)}
              >
                <Label>Password</Label>
                <Input type="password" autoComplete="new-password" />
                {touched.password && errors.password && (
                  <FieldError>{errors.password}</FieldError>
                )}
              </TextField>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <Button
                type="submit"
                variant="primary"
                fullWidth
                isDisabled={isSubmitting}
              >
                {isSubmitting ? <Spinner size="sm" /> : "Create Account"}
              </Button>
              <p className="text-center text-sm text-gray-500">
                Already have an account?{" "}
                <Link
                  href="/login"
                  className="text-blue-600 font-medium hover:underline"
                >
                  Sign In
                </Link>
              </p>
            </form>
          )}
        </Formik>
      </Card.Content>
    </Card>
  );
}
