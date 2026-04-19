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
import { LoginSchema } from "@/helpers/schemas";
import { loginWithForm } from "@/lib/auth.api";
import { createAuthCookie } from "@/actions/auth.action";

export function Login() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  return (
    <Card className="w-full max-w-md p-6">
      <Card.Header className="pb-2">
        <Card.Title className="text-2xl">Sign in to Colony</Card.Title>
        <Card.Description>Manage your expenses</Card.Description>
      </Card.Header>
      <Card.Content>
        <Formik
          initialValues={{ email: "", password: "" }}
          validationSchema={LoginSchema}
          onSubmit={async (values, { setSubmitting }) => {
            setError(null);
            const result = await loginWithForm(values.email, values.password);
            if (result.success) {
              await createAuthCookie(result.data.access_token);
              router.replace("/cycles");
            } else {
              setError(result.error.message);
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
                <Input type="password" autoComplete="current-password" />
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
                {isSubmitting ? <Spinner size="sm" /> : "Sign In"}
              </Button>
              <p className="text-center text-sm text-gray-500">
                Don&apos;t have an account?{" "}
                <Link
                  href="/register"
                  className="text-blue-600 font-medium hover:underline"
                >
                  Register
                </Link>
              </p>
            </form>
          )}
        </Formik>
      </Card.Content>
    </Card>
  );
}
